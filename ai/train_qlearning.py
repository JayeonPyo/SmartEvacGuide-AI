"""
Q-Learning 강화학습 알고리즘
경로 선택 정책 학습 - 5000 에피소드 버전
"""

import numpy as np
import pickle
from collections import defaultdict
from rl_environment import EvacuationEnv

class QLearningAgent:
    def __init__(self, learning_rate=0.15, discount=0.95, epsilon=0.15):
        """
        Q-Learning 에이전트 - 최적화된 파라미터
        
        Args:
            learning_rate: 학습률 (0.15 - 빠른 학습)
            discount: 할인율 (0.95)
            epsilon: 탐험 확률 (0.15 - 적은 탐험)
        """
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        
        # Q-테이블 (상태, 행동) -> 가치
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        print(f"[RL] Q-Learning 에이전트 초기화")
        print(f"     학습률={self.lr}, 할인율={self.gamma}, 탐험={self.epsilon}")
    
    def get_action(self, state, valid_routes, training=True):
        """
        행동 선택 (epsilon-greedy)
        
        Args:
            state: 현재 상태 (disaster, crowd, location)
            valid_routes: 가능한 경로 리스트
            training: 학습 중인지 여부
        
        Returns:
            route_id: 선택한 경로
        """
        # 학습 중이고 랜덤 탐험
        if training and np.random.random() < self.epsilon:
            return np.random.choice(valid_routes)
        
        # 최선의 행동 선택 (exploitation)
        q_values = {route: self.q_table[state][route] 
                   for route in valid_routes}
        
        max_q = max(q_values.values())
        
        # 최대값 가진 행동들
        best_routes = [route for route, q in q_values.items() 
                      if q == max_q]
        
        return np.random.choice(best_routes)
    
    def update(self, state, action, reward, next_state=None):
        """
        Q-테이블 업데이트
        
        Q(s,a) = Q(s,a) + lr * (reward - Q(s,a))
        """
        current_q = self.q_table[state][action]
        
        # TD 업데이트
        td_target = reward  # 종료 상태
        td_error = td_target - current_q
        
        # 업데이트
        self.q_table[state][action] = current_q + self.lr * td_error
    
    def save(self, filepath):
        """Q-테이블 저장"""
        with open(filepath, 'wb') as f:
            pickle.dump(dict(self.q_table), f)
        print(f"[RL] Q-테이블 저장: {filepath}")
    
    def load(self, filepath):
        """Q-테이블 로드"""
        try:
            with open(filepath, 'rb') as f:
                self.q_table = defaultdict(lambda: defaultdict(float), 
                                          pickle.load(f))
            print(f"[RL] Q-테이블 로드: {filepath}")
            return True
        except:
            print(f"[RL] Q-테이블 로드 실패")
            return False


def train(episodes=5000, print_every=500):
    """
    Q-Learning 학습
    
    Args:
        episodes: 학습 에피소드 수 (5000)
        print_every: 출력 주기 (500)
    """
    env = EvacuationEnv()
    agent = QLearningAgent()
    
    print("\n" + "=" * 60)
    print(f"Q-Learning 학습 시작 ({episodes} 에피소드)")
    print("=" * 60)
    
    rewards_history = []
    
    for episode in range(episodes):
        # 에피소드 시작
        state = env.reset()
        valid_routes = env.get_valid_routes()
        
        # 행동 선택
        action = agent.get_action(state, valid_routes, training=True)
        
        # 환경 실행
        reward, done = env.step(action)
        
        # Q-테이블 업데이트
        agent.update(state, action, reward)
        
        # 기록
        rewards_history.append(reward)
        
        # 출력
        if (episode + 1) % print_every == 0:
            avg_reward = np.mean(rewards_history[-print_every:])
            print(f"에피소드 {episode+1}/{episodes} | "
                  f"평균 보상: {avg_reward:.2f}")
    
    print("\n" + "=" * 60)
    print("학습 완료!")
    print("=" * 60)
    
    # Q-테이블 저장 (현재 폴더)
    agent.save('./q_table.pkl')
    
    return agent


def test_agent(agent, num_tests=20):
    """학습된 에이전트 테스트"""
    env = EvacuationEnv()
    
    print("\n" + "=" * 60)
    print("학습된 에이전트 테스트")
    print("=" * 60)
    
    total_reward = 0
    
    for i in range(num_tests):
        state = env.reset()
        valid_routes = env.get_valid_routes()
        
        # 학습된 정책으로 행동 (탐험 없음)
        action = agent.get_action(state, valid_routes, training=False)
        
        reward, done = env.step(action)
        total_reward += reward
        
        disaster, crowd, location = state
        print(f"\n테스트 {i+1}:")
        print(f"  상태: {disaster} / {crowd}명 / {location}")
        print(f"  선택: 경로 {action}")
        print(f"  보상: {reward:.2f}")
    
    avg_reward = total_reward / num_tests
    print(f"\n평균 보상: {avg_reward:.2f}")
    
    return avg_reward


if __name__ == "__main__":
    # 5000 에피소드 학습
    agent = train(episodes=5000, print_every=500)
    
    # 20번 테스트
    test_agent(agent, num_tests=20)