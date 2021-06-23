''' Register new environments
'''
from CFR.envs.env import Env
from CFR.envs.registration import register, make

register(
    env_id='guandan',
    entry_point='CFR.envs.guandan:GuandanEnv',
)
