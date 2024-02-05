from __future__ import division, absolute_import
import copy
import numpy as np
import random
from collections import defaultdict
from torch.utils.data.sampler import Sampler, RandomSampler, SequentialSampler

AVAI_SAMPLERS = ['RandomIdentitySampler', 'SequentialSampler', 'RandomSampler']


class RandomIdentitySampler(Sampler):
    """Randomly samples N identities each with K instances.

    Args:
        data_source (list): contains tuples of (img_path(s), pid, camid).
        batch_size (int): batch size.
        num_instances (int): number of instances per identity in a batch.
    """

    def __init__(self, data_source, batch_size, num_instances):
        if batch_size < num_instances:
            raise ValueError(
                'batch_size={} must be no less '
                'than num_instances={}'.format(batch_size, num_instances)
            )

        self.data_source = data_source
        self.batch_size = batch_size
        self.num_instances = num_instances
        self.num_pids_per_batch = self.batch_size // self.num_instances
        self.index_dic = defaultdict(list)
        self.game_dic = {}
        for index, sample in enumerate(self.data_source):
            self.index_dic[sample['pid']].append(index)
            if sample['camid'] not in self.game_dic.keys():
                self.game_dic[sample['camid']] = defaultdict(list)
            self.game_dic[sample['camid']][sample['pid']].append(index)

        self.pids = list(self.index_dic.keys())
        self.gids = list(self.game_dic.keys())

        # estimate number of examples in an epoch
        self.length = 0
        for pid in self.pids:
            idxs = self.index_dic[pid]
            num = len(idxs)
            if num < self.num_instances:
                num = self.num_instances
            self.length += num - num % self.num_instances

    def __iter__(self):
        batch_idxs_dict = defaultdict(list)
        batch_games_dic = copy.deepcopy(self.game_dic)

        for pid in self.pids:
            idxs = copy.deepcopy(self.index_dic[pid])
            if len(idxs) < self.num_instances:
                idxs = np.random.choice(
                    idxs, size=self.num_instances, replace=True
                )
            random.shuffle(idxs)
            batch_idxs = []
            for idx in idxs:
                batch_idxs.append(idx)
                if len(batch_idxs) == self.num_instances:
                    batch_idxs_dict[pid].append(batch_idxs)
                    batch_idxs = []

        avai_gids = copy.deepcopy(self.gids)
        final_idxs = []

        while len(avai_gids) > 0:
            selected_game = random.sample(avai_gids, 1)[0]
            avai_pids = copy.deepcopy([i for i in batch_games_dic[selected_game].keys()])
            selected_pids = random.sample(avai_pids, self.num_pids_per_batch)
            for pid in selected_pids:
                batch_idxs = batch_idxs_dict[pid].pop(0)
                final_idxs.extend(batch_idxs)

                if len(batch_idxs_dict[pid]) == 0:
                    del batch_idxs_dict[pid]
                    del batch_games_dic[selected_game][pid]

            if len(batch_games_dic[selected_game].keys()) < self.num_pids_per_batch:
                    avai_gids.remove(selected_game)

        return iter(final_idxs)

    def __len__(self):
        return self.length



class PrtreidSampler(Sampler):
    """Samples for all three tasks: reid, role, and team

    Args:
        data_source (list): contains tuples of (img_path(s), pid, camid).
        batch_size (int): batch size.
        num_instances (int): number of instances per identity in a batch.
    """

    def __init__(self, data_source, batch_size, num_instances):
        if batch_size < num_instances:
            raise ValueError(
                'batch_size={} must be no less '
                'than num_instances={}'.format(batch_size, num_instances)
            )

        self.data_source = data_source
        self.batch_size = batch_size
        self.num_instances = num_instances
        self.num_pids_per_batch = self.batch_size // self.num_instances
        self.index_dic = defaultdict(list)
        self.game_dic = {}
        for index, sample in enumerate(self.data_source):
            self.index_dic[sample['pid']].append(index)
            if sample['camid'] not in self.game_dic.keys():
                self.game_dic[sample['camid']] = {'0': defaultdict(list), '1': defaultdict(list), '2': defaultdict(list)}

            if sample['role'] == 0:
                if sample['team'] %2 == 0:
                    self.game_dic[sample['camid']]['0'][sample['pid']].append(index)
                else:
                    self.game_dic[sample['camid']]['1'][sample['pid']].append(index)
            else:
                self.game_dic[sample['camid']]['2'][sample['pid']].append(index)

        self.pids = list(self.index_dic.keys())
        self.gids = list(self.game_dic.keys())

        # estimate number of examples in an epoch
        self.length = 0
        for pid in self.pids:
            idxs = self.index_dic[pid]
            num = len(idxs)
            if num < self.num_instances:
                num = self.num_instances
            self.length += num - num % self.num_instances

    def __iter__(self):
        batch_idxs_dict = defaultdict(list)
        batch_games_dic = copy.deepcopy(self.game_dic)

        for pid in self.pids:
            idxs = copy.deepcopy(self.index_dic[pid])
            if len(idxs) < self.num_instances:
                idxs = np.random.choice(
                    idxs, size=self.num_instances, replace=True
                )
            random.shuffle(idxs)
            batch_idxs = []
            for idx in idxs:
                batch_idxs.append(idx)
                if len(batch_idxs) == self.num_instances:
                    batch_idxs_dict[pid].append(batch_idxs)
                    batch_idxs = []

        avai_gids = copy.deepcopy(self.gids)
        final_idxs = []

        while len(avai_gids) > 0:
            selected_game = random.sample(avai_gids, 1)[0]
            ################### from left side ############################
            avai_pids = copy.deepcopy([i for i in batch_games_dic[selected_game]['0'].keys()])
            selected_pids = random.sample(avai_pids, 3)
            ################### from right side ###########################
            avai_pids = copy.deepcopy([i for i in batch_games_dic[selected_game]['1'].keys()])
            selected_pids += random.sample(avai_pids, 3)
            ################## from other roles ###########################
            avai_pids = copy.deepcopy([i for i in batch_games_dic[selected_game]['2'].keys()])
            selected_pids += random.sample(avai_pids, 2)

            for pid in selected_pids:
                batch_idxs = batch_idxs_dict[pid].pop(0)
                if pid in batch_games_dic[selected_game]['2']:
                    batch_idxs_dict[pid].append(batch_idxs)

                final_idxs.extend(batch_idxs)

                if len(batch_idxs_dict[pid]) == 0:
                    del batch_idxs_dict[pid]
                    if '0' in batch_games_dic[selected_game].keys() and pid in batch_games_dic[selected_game]['0']:
                        del batch_games_dic[selected_game]['0'][pid]
                        if len(batch_games_dic[selected_game]['0']) < 3:
                            del batch_games_dic[selected_game]['0']

                    elif '1' in batch_games_dic[selected_game].keys() and pid in batch_games_dic[selected_game]['1']:
                        del batch_games_dic[selected_game]['1'][pid]
                        if len(batch_games_dic[selected_game]['1']) < 3:
                            del batch_games_dic[selected_game]['1']

                    elif '2' in batch_games_dic[selected_game].keys() and pid in batch_games_dic[selected_game]['2']:
                        del batch_games_dic[selected_game]['2'][pid]
                        if len(batch_games_dic[selected_game]['2']) < 2:
                            del batch_games_dic[selected_game]['2']

            if len(batch_games_dic[selected_game].keys()) < 3:
                    avai_gids.remove(selected_game)

        return iter(final_idxs)

    def __len__(self):
        return self.length





def build_train_sampler(
    data_source, train_sampler, batch_size=32, num_instances=4, **kwargs
):
    """Builds a training sampler.

    Args:
        data_source (list): contains tuples of (img_path(s), pid, camid).
        train_sampler (str): sampler name (default: ``RandomSampler``).
        batch_size (int, optional): batch size. Default is 32.
        num_instances (int, optional): number of instances per identity in a
            batch (when using ``RandomIdentitySampler``). Default is 4.
    """
    assert train_sampler in AVAI_SAMPLERS, \
        'train_sampler must be one of {}, but got {}'.format(AVAI_SAMPLERS, train_sampler)

    if train_sampler == 'RandomIdentitySampler':
        sampler = PrtreidSampler(data_source, batch_size, num_instances)

    elif train_sampler == 'SequentialSampler':
        sampler = SequentialSampler(data_source)

    elif train_sampler == 'RandomSampler':
        sampler = RandomSampler(data_source)

    #sampler = RandomIdentityAndTeamSampler(data_source, 64, 4, 4)

    return sampler
