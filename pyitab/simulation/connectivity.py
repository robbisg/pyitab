import numpy as np
import itertools


class ConnectivityStateSimulator():

    def __init__(self, n_nodes=10, max_edges=5, fsamp=128):
    
        edges = [e for e in itertools.combinations(np.arange(n_nodes), 2)]
        n_edges = len(edges)

        states = []
        for i in range(max_edges):
            states += [e for e in itertools.combinations(np.arange(n_edges), i+1)]

        states = np.array(states)

        self._edges = edges
        self._n_edges = len(edges)
        self._states = states
        self._n_states = len(states)

        self._n_nodes = n_nodes
        self._max_edges = max_edges
        self._fs = fsamp



    def fit(self, n_brain_states=6, length_states=100, min_time=2.5, max_time=3.5):

        # Randomize random stuff

        states_idx = np.random.randint(0, self._n_states, n_brain_states)        
        
        selected_states = self._states[states_idx]

        bs_length = np.random.randint(self._fs * min_time, 
                                      self._fs * max_time, 
                                      length_states
                                      )

        # This is done using Hidden Markov Models but since 
        # Transition matrix is uniformly distributed we can use random sequency
        #     mc = mcmix(nBS,'Fix',ones(nBS)*(1/nBS));
        #     seqBS= simulate(mc,nbs_sequence-1);
        bs_sequence = np.random.randint(0, n_brain_states, length_states)

        bs_dynamics = [] 
        for i, time in enumerate(bs_length): 
            for _ in range(time): 
                bs_dynamics.append(bs_sequence[i])
        bs_dynamics = np.array(bs_dynamics)

        brain_matrices = []
        for j in range(n_brain_states):
            matrix = np.eye(self._n_nodes)
            selected_edges = selected_states[j]
            for edge in selected_edges:
                matrix[self._edges[np.array(edge)]] = 1
            brain_matrices.append(matrix)

        brain_matrices = np.array(brain_matrices)

        self._states = brain_matrices
        self._state_length = bs_length
        self._state_sequence = bs_sequence
        self._dynamics = bs_dynamics

        return self