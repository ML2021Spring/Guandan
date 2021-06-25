''' An example of solve Leduc Hold'em with CFR (chance sampling)
'''
import os
import argparse
import shutil
# import tensorflow as tf
from numba import jit

import CFR
from CFR.agents import CFRAgent, RandomAgent
from CFR.utils import set_seed, tournament, Logger, plot_curve


def ignore(path, content_list):
    return [
    ]


def train(args):
    # Make environments, CFR only supports Leduc Holdem
    env = CFR.make('guandan', config={'allow_step_back': True})
    eval_env = CFR.make('guandan', config={})

    # Seed numpy, torch, random
    set_seed(args.seed)

    # Initilize CFR Agent
    agent = CFRAgent(env, os.path.join(args.log_dir, 'cfr_model_0'))
    agent.load()  # If we have saved model, we first load the model

    # agents = []
    # agent0 = CFRAgent(env, os.path.join(args.log_dir, 'cfr_model_0'))
    # agent0.load()
    # agents.append(agent0)
    # agent1 = CFRAgent(env, os.path.join(args.log_dir, 'cfr_model_1'))
    # agent1.load()
    # agents.append(agent1)
    # agent2 = CFRAgent(env, os.path.join(args.log_dir, 'cfr_model_2'))
    # agent2.load()
    # agents.append(agent2)
    # agent3 = CFRAgent(env, os.path.join(args.log_dir, 'cfr_model_3'))
    # agent3.load()
    # agents.append(agent3)
    # Evaluate CFR against random
    eval_env.set_agents(
        [agent, RandomAgent(num_actions=env.num_actions), agent,
         RandomAgent(num_actions=env.num_actions)])

    # eval_env.set_agents(agents)
    # Start training
    with Logger(args.log_dir) as logger:
        for episode in range(args.num_episodes):
            agent.train()
            print('\rIteration {}\n'.format(episode), end='')
            # Evaluate the performance. Play with Random agents.
            if episode % args.evaluate_every == 0:
                agent.save()  # Save model
                reward, win_rob = tournament(eval_env, args.num_eval_games)
                logger.log_performance(episode, env.timestep, reward[0], win_rob[0])
            if episode % 50 == 0:
                if os.path.exists("res3"):
                    shutil.rmtree("res3")
                shutil.copytree(args.log_dir, "res3", ignore=ignore)

        # Get the paths
        csv_path, fig_path = logger.csv_path, logger.fig_path
    # Plot the learning curve
    plot_curve(csv_path, fig_path, 'cfr')


@jit(forceobj=True)
def main():
    parser = argparse.ArgumentParser("CFR example in RLCard")
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--num_episodes', type=int, default=5000)
    parser.add_argument('--num_eval_games', type=int, default=100)
    parser.add_argument('--evaluate_every', type=int, default=100)
    parser.add_argument('--log_dir', type=str, default='experiments/guandan_cfr_result6/')

    args = parser.parse_args()

    train(args)


if __name__ == '__main__':
    # with tf.device('/device:GPU:0'):
    main()
