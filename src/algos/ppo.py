import torch
import torch.nn as nn
from torch.distributions import Categorical
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class Memory:
    def __init__(self):
        self.actions = []
        self.states = []
        self.logprobs = []
        self.rewards = []
        self.is_terminals = []
    
    def clear_memory(self):
        del self.actions[:]
        del self.states[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.is_terminals[:]

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, n_latent_var):
        super(ActorCritic, self).__init__()

        # actor
        self.action_layer = nn.Sequential(
                nn.Linear(state_dim, n_latent_var),
                nn.ReLU(),
                nn.LayerNorm(n_latent_var),
                #nn.Dropout(0.2),
                nn.Linear(n_latent_var, n_latent_var),
                nn.ReLU(),
                nn.LayerNorm(n_latent_var),
                nn.Linear(n_latent_var, n_latent_var),
                nn.ReLU(),
                nn.LayerNorm(n_latent_var),
                #nn.Dropout(0.2),
                nn.Linear(n_latent_var, action_dim),
                nn.Softmax()
                )
        
        # critic
        self.value_layer = nn.Sequential(
                nn.Linear(state_dim, n_latent_var),
                nn.ReLU(),
                nn.LayerNorm(n_latent_var),
                #nn.Dropout(0.2),
                nn.Linear(n_latent_var, n_latent_var),
                nn.ReLU(),
                nn.LayerNorm(n_latent_var),
                nn.Linear(n_latent_var, n_latent_var),
                nn.ReLU(),
                nn.LayerNorm(n_latent_var),
                #nn.Dropout(0.2),
                nn.Linear(n_latent_var, 1)
                )
        
    def forward(self):
        raise NotImplementedError
        
    def act(self, state, memory, eval = False):
        state = torch.from_numpy(state).float().to(device) 
        if torch.isnan(state).any():
            #state[state!=state]  = 0.0
            state = torch.where(torch.isnan(state), torch.zeros_like(state), state)
        #print(state)
        action_probs = self.action_layer(state)
        action_probs = torch.clamp(action_probs, 0, 1)
        #print(action_probs)
        if(torch.isnan(action_probs).any()):
            print('ho there ')
            print(action_probs)
        dist = Categorical(action_probs)
        #print(dist.sample())

        action = dist.sample()
        #print(dist.log_prob(action))
        if not eval:
            memory.states.append(state)
            memory.actions.append(action)
            memory.logprobs.append(dist.log_prob(action))
            
        return action.item()
    
    def evaluate(self, state, action):
        action_probs = self.action_layer(state)
        dist = Categorical(action_probs)
        
        action_logprobs = dist.log_prob(action)
        dist_entropy = dist.entropy()
        
        state_value = self.value_layer(state)
        
        return action_logprobs, torch.squeeze(state_value), dist_entropy
        
class PPO:
    def __init__(self, state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip):
        self.lr = lr
        self.betas = betas
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs
        
        self.policy = ActorCritic(state_dim, action_dim, n_latent_var).to(device)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=lr, betas=betas,)
        self.policy_old = ActorCritic(state_dim, action_dim, n_latent_var).to(device)
        self.policy_old.load_state_dict(self.policy.state_dict())
        
        self.MseLoss = nn.MSELoss()
        self.BCELoss = nn.BCELoss()
    def get_lr(self,):
        for param_group in self.optimizer.param_groups:
            print(param_group['lr'])
            return param_group['lr']
    
    def update(self, memory):   
        # Monte Carlo estimate of state rewards:
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(memory.rewards), reversed(memory.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            #print(reward,self.gamma , discounted_reward)
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.insert(0, discounted_reward)
        
        # Normalizing the rewards:
        rewards = torch.tensor(rewards, dtype=torch.float32).to(device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)
        
        # convert list to tensor
        old_states = torch.stack(memory.states).to(device).detach()
        old_actions = torch.stack(memory.actions).to(device).detach()
        old_logprobs = torch.stack(memory.logprobs).to(device).detach()
        
        # Optimize policy for K epochs:
        for _ in range(self.K_epochs):
            # Evaluating old actions and values :
            logprobs, state_values, dist_entropy = self.policy.evaluate(old_states, old_actions)
            
            # Finding the ratio (pi_theta / pi_theta__old):
            ratios = torch.exp(logprobs - old_logprobs.detach())
                
            # Finding Surrogate Loss:
            advantages = rewards - state_values.detach()
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantages
            loss = -torch.min(surr1, surr2) + 0.5*self.MseLoss(state_values, rewards) - 0.01*dist_entropy
            
            # take gradient step
            self.optimizer.zero_grad()
            loss.mean().backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 5.)
            self.optimizer.step()
        
        # Copy new weights into old policy:
        #print(self.policy.parameters())
        self.policy_old.load_state_dict(self.policy.state_dict())
    
        
