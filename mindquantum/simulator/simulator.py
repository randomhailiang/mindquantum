# -*- coding: utf-8 -*-
# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Simulator."""
from mindquantum.core.gates.basic import BasicGate
import numpy as np
from mindquantum.core.circuit import Circuit
from mindquantum.core.operators import Hamiltonian
from mindquantum.core.operators.hamiltonian import MODE
from mindquantum.core.parameterresolver import ParameterResolver
from mindquantum.core.parameterresolver.parameterresolver import _check_and_generate_pr_type
from mindquantum.core.gates import MeasureResult
from mindquantum.core.gates import Measure
from mindquantum.core.gates import BarrierGate
from mindquantum.utils import ket_string
from mindquantum import mqbackend as mb

SUPPORTED_SIMULATOR = ['projectq']


def get_supported_simulator():
    """Get simulator name that supported by MindQuantum """
    return SUPPORTED_SIMULATOR


class Simulator:
    """
    Quantum simulator that simulate quantum circuit.

    Args:
        backend (str): which backend you want. The supported backend can be found
            in SUPPORTED_SIMULATOR
        n_qubits (int): number of quantum simulator.
        seed (int): the random seed for this simulator. Default: 42.

    Examples:
        >>> from mindquantum import Simulator
        >>> from mindquantum import qft
        >>> sim = Simulator('projectq', 2)
        >>> sim.apply_circuit(qft(range(2)))
        >>> sim.get_qs()
        array([0.5+0.j, 0.5+0.j, 0.5+0.j, 0.5+0.j])
    """
    def __init__(self, backend, n_qubits, seed=42):
        if not isinstance(backend, str):
            raise TypeError(f"backend need a string, but get {type(backend)}")
        if backend not in SUPPORTED_SIMULATOR:
            raise ValueError(f"backend {backend} not supported!")
        if not isinstance(n_qubits, int) or n_qubits < 0:
            raise ValueError(f"n_qubits of simulator should be a non negative int, but get {n_qubits}")
        if not isinstance(seed, int) or seed < 0 or seed > 2**32 - 1:
            raise ValueError(f"seed must be between 0 and 2**32 - 1")
        self.backend = backend
        self.seed = seed
        self.n_qubits = n_qubits
        if backend == 'projectq':
            self.sim = mb.projectq(seed, n_qubits)

    def __str__(self):
        state = self.get_qs()
        s = f"{self.backend} simulator with {self.n_qubits} qubit{'s' if self.n_qubits > 1 else ''}."
        s += f"\nCurrent quantum state:\n"
        if self.n_qubits < 4:
            s += '\n'.join(ket_string(state))
        else:
            s += state.__str__()
        return s

    def __repr__(self):
        return self.__str__()

    def reset(self):
        """
        Reset simulator to zero state.

        Examples:
            >>> from mindquantum import Simulator
            >>> from mindquantum import qft
            >>> sim = Simulator('projectq', 2)
            >>> sim.apply_circuit(qft(range(2)))
            >>> sim.reset()
            >>> sim.get_qs()
            array([1.+0.j, 0.+0.j, 0.+0.j, 0.+0.j])
        """
        self.sim.reset()

    def flush(self):
        """
        Flush gate that works for projectq simulator. The projectq simulator
        will cache several gate and fushion these gate into a bigger gate, and
        than act on the quantum state. The flush command will ask the simulator
        to fushion currently stored gate and act on the quantum state.

        Examples:
            >>> from mindquantum import Simulator
            >>> from mindquantum import H
            >>> sim = Simulator('projectq', 1)
            >>> sim.apply_gate(H.on(0))
            >>> sim.flush()
        """
        if self.backend == 'projectq':
            self.sim.run()

    def apply_gate(self, gate, pr=None):
        """
        Apply a gate on this simulator, can be a quantum gate or a measurement operator

        Args:
            gate (BasicGate): The gate you want to apply.
            pr (Union[numbers.Number, numpy.ndarray, ParameterResolver]): The
                parameter for parameterized gate. Default: None.

        Returns:
            int or None, if the gate if a measure gate, then return a collapsed state, Otherwise
            return None.

        Examples:
            >>> import numpy as np
            >>> from mindquantum import Simulator
            >>> from mindquantum import RY, Measure
            >>> sim = Simulator('projectq', 1)
            >>> sim.apply_gate(RY('a').on(0), np.pi/2)
            >>> sim.get_qs()
            array([0.70710678+0.j, 0.70710678+0.j])
            >>> sim.apply_gate(Measure().on(0))
            1
            >>> sim.get_qs()
            array([0.+0.j, 1.+0.j])
        """
        if not isinstance(gate, BasicGate):
            raise TypeError(f"gate requires a quantum gate, but get {type(gate)}")
        if not isinstance(gate, BarrierGate):
            gate_max = max(max(gate.obj_qubits, gate.ctrl_qubits))
            if self.n_qubits < gate_max:
                raise ValueError(f"qubits of gate {gate} is higher than simulator qubits.")
            if isinstance(gate, Measure):
                return self.sim.apply_measure(gate.get_cpp_obj())
            if pr is None:
                if gate.parameterized:
                    raise ValueError("apply a parameterized gate needs a parameter_resolver")
                self.sim.apply_gate(gate.get_cpp_obj())
            else:
                pr = _check_and_generate_pr_type(pr, gate.coeff.params_name)
                self.sim.apply_gate(gate.get_cpp_obj(), pr.get_cpp_obj(), False)
        return None

    def apply_circuit(self, circuit, pr=None):
        """
        Apply a circuit on this simulator.

        Args:
            circuit (Circuit): The quantum circuit you want to apply on this simulator.
            pr (Union[ParameterResolver, dict, numpy.ndarray]): The
                parameter resolver for this circuit. If the circuit is not parameterized,
                this arg should be None. Default: None.

        Returns:
            MeasureResult or None, if the circuit has measure gate, then return a MeasureResult,
            otherwise return None.

        Examples:
            >>> import numpy as np
            >>> from mindquantum import Circuit, H
            >>> from mindquantum import Simulator
            >>> sim = Simulator('projectq', 2)
            >>> sim.apply_circuit(Circuit().un(H, 2))
            >>> sim.apply_circuit(Circuit().ry('a', 0).ry('b', 1), np.array([1.1, 2.2]))
            >>> sim
            projectq simulator with 2 qubits.
            Current quantum state:
            -0.0721702531972066¦00⟩
            -0.30090405886869676¦01⟩
            0.22178317006196263¦10⟩
            0.9246947752567126¦11⟩
            >>> sim.apply_circuit(Circuit().measure(0).measure(1))
            shots: 1
            Keys: q1 q0│0.00     0.2         0.4         0.6         0.8         1.0
            ───────────┼───────────┴───────────┴───────────┴───────────┴───────────┴
                     11│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
                       │
            {'11': 1}
        """
        if not isinstance(circuit, Circuit):
            raise TypeError(f"circuit must be Circuit, but get {type(Circuit)}")
        if self.n_qubits < circuit.n_qubits:
            raise ValueError(f"Circuit has {circuit.n_qubits} qubits, which is more than simulator qubits.")
        if circuit.has_measure:
            res = MeasureResult()
            res.add_measure(circuit.all_measures.keys())
        if pr is None:
            if circuit.params_name:
                raise ValueError("Applying a parameterized circuit needs a parameter_resolver")
            if circuit.has_measure:
                pr = ParameterResolver()
                samples = np.array(
                    self.sim.apply_circuit_with_measure(circuit.get_cpp_obj(), pr.get_cpp_obj(), res.keys_map)).reshape(
                        (1, -1))
                res.collect_data(samples)
                return res
            self.sim.apply_circuit(circuit.get_cpp_obj())
        else:
            if not isinstance(pr, (ParameterResolver, dict, np.ndarray)):
                raise TypeError(f"parameter_resolver requires a ParameterResolver, but get {type(pr)}")
            if isinstance(pr, dict):
                pr = ParameterResolver(pr)
            if isinstance(pr, np.ndarray):
                if len(pr.shape) != 1 or pr.shape[0] != len(circuit.params_name):
                    raise ValueError(f"size of parameters input ({pr.shape}) not\
match with circuit parameters ({len(circuit.params_name)}, )")
                pr = ParameterResolver(dict(zip(circuit.params_name, pr)))
            if circuit.has_measure:
                samples = np.array(
                    self.sim.apply_circuit_with_measure(circuit.get_cpp_obj(), pr.get_cpp_obj(), res.keys_map)).reshape(
                        (1, -1))
                res.collect_data(samples)
                return res
            self.sim.apply_circuit(circuit.get_cpp_obj(), pr.get_cpp_obj())
        return None

    def sampling(self, circuit, pr=None, shots=1, seed=None):
        """
        Samping the measure qubit in circuit. Sampling do not change the origin quantum
        state of this simulator.

        Args:
            circuit (Circuit): The circuit that you want to evolution and do sampling.
            pr (Union[None, dict, ParameterResolver]): The parameter
                resolver for this circuit, if this circuit is a parameterized circuit.
                Default: None.
            shots (int): How many shots you want to sampling this circuit. Default: 1
            seed (int): Random seed for random sampling. Default: None.

        Returns:
            MeasureResult, the measure result of sampling.

        Examples:
            >>> from mindquantum import Circuit, Measure
            >>> from mindquantum import Simulator
            >>> circ = Circuit().ry('a', 0).ry('b', 1)
            >>> circ += Measure('q0_0').on(0)
            >>> circ += Measure('q0_1').on(0)
            >>> circ += Measure('q1').on(1)
            >>> sim = Simulator('projectq', circ.n_qubits)
            >>> res = sim.sampling(circ, {'a': 1.1, 'b': 2.2}, shots=100, seed=42)
            >>> res
            shots: 100
            Keys: q1 q0_1 q0_0│0.00   0.122       0.245       0.367        0.49       0.612
            ──────────────────┼───────────┴───────────┴───────────┴───────────┴───────────┴
                           000│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
                              │
                           011│▒▒▒▒▒▒▒
                              │
                           100│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
                              │
                           111│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
                              │
            {'000': 17, '011': 8, '100': 49, '111': 26}
        """
        if not isinstance(circuit, Circuit):
            raise TypeError(f"sampling circuit need a quantum circuit but get {type(circuit)}")
        if self.n_qubits < circuit.n_qubits:
            raise ValueError(f"Circuit has {circuit.n_qubits} qubits, which is more than simulator qubits.")
        if not isinstance(shots, int) or shots < 0:
            raise ValueError(f"sampling shot should be non negative int, but get {shots}")
        if circuit.parameterized:
            if pr is None:
                raise ValueError("Sampling a parameterized circuit need a ParameterResolver")
            pr = ParameterResolver(pr)
        else:
            pr = ParameterResolver()
        if seed is None:
            seed = self.seed
        elif not isinstance(seed, int) or seed < 0 or seed > 2**23 - 1:
            raise ValueError(f"seed must be between 0 and 2**23 - 1")
        res = MeasureResult()
        res.add_measure(circuit.all_measures.keys())
        samples = np.array(self.sim.sampling(circuit.get_cpp_obj(), pr.get_cpp_obj(), shots, res.keys_map,
                                             seed)).reshape((shots, -1))
        res.collect_data(samples)
        return res

    def apply_hamiltonian(self, hamiltonian: Hamiltonian):
        """
        Apply hamiltonian to a simulator, this hamiltonian can be
        hermitian or non hermitian.

        Notes:
            The quantum state may be not a normalized quantum state after apply hamiltonian.

        Args:
            hamiltonian (Hamiltonian): the hamiltonian you want to apply.

        Examples:
            >>> from mindquantum import Simulator
            >>> from mindquantum import Circuit, Hamiltonian
            >>> from mindquantum.core.operators import QubitOperator
            >>> import scipy.sparse as sp
            >>> sim = Simulator('projectq', 1)
            >>> sim.apply_circuit(Circuit().h(0))
            >>> sim.get_qs()
            array([0.70710678+0.j, 0.70710678+0.j])
            >>> ham1 = Hamiltonian(QubitOperator('Z0'))
            >>> sim.apply_hamiltonian(ham1)
            >>> sim.get_qs()
            array([ 0.70710678+0.j, -0.70710678+0.j])

            >>> sim.reset()
            >>> ham2 = Hamiltonian(sp.csr_matrix([[1, 2], [3, 4]]))
            >>> sim.apply_hamiltonian(ham2)
            >>> sim.get_qs()
            array([1.+0.j, 3.+0.j])
        """

        if not isinstance(hamiltonian, Hamiltonian):
            raise TypeError(f"hamiltonian requires a Hamiltonian, but got {type(hamiltonian)}")
        _check_hamiltonian_qubits_number(hamiltonian, self.n_qubits)
        self.sim.apply_hamiltonian(hamiltonian.get_cpp_obj())

    def get_expectation(self, hamiltonian):
        r"""
        Get expectation of the given hamiltonian. The hamiltonian could be non hermitian.

        .. math::

            E = \left<\psi\right|H\left|\psi\right>

        Args:
            hamiltonian (Hamiltonian): The hamiltonian you want to get expectation.

        Returns:
            numbers.Number, the expectation value.

        Examples:
            >>> from mindquantum.core.operators import QubitOperator
            >>> from mindquantum import Circuit, Simulator
            >>> from mindquantum import Hamiltonian
            >>> sim = Simulator('projectq', 1)
            >>> sim.apply_circuit(Circuit().ry(1.2, 0))
            >>> ham = Hamiltonian(QubitOperator('Z0'))
            >>> sim.get_expectation(ham)
            (0.36235775447667357+0j)
        """
        if not isinstance(hamiltonian, Hamiltonian):
            raise TypeError(f"hamiltonian requires a Hamiltonian, but got {type(hamiltonian)}")
        _check_hamiltonian_qubits_number(hamiltonian, self.n_qubits)
        return self.sim.get_expectation(hamiltonian.get_cpp_obj())

    def get_qs(self, ket=False):
        """
        Get current quantum state of this simulator.

        Returns:
            numpy.ndarray, the current quantum state.

        Examples:
            >>> from mindquantum import qft, Simulator
            >>> sim = Simulator('projectq', 2)
            >>> sim.apply_circuit(qft(range(2)))
            >>> sim.get_qs()
            array([0.5+0.j, 0.5+0.j, 0.5+0.j, 0.5+0.j])
        """
        state = np.array(self.sim.get_qs())
        if ket:
            return '\n'.join(ket_string(state))
        return state

    def set_qs(self, vec):
        """
        Set quantum state for this simulation.

        Args:
            vec (numpy.ndarray): the quantum state that you want.

        Examples:
            >>> from mindquantum import Simulator
            >>> import numpy as np
            >>> sim = Simulator('projectq', 1)
            >>> sim.get_qs()
            array([1.+0.j, 0.+0.j])
            >>> sim.set_qs(np.array([1, 1]))
            >>> sim.get_qs()
            array([0.70710678+0.j, 0.70710678+0.j])
        """
        if not isinstance(vec, np.ndarray):
            raise TypeError(f"quantum state must be a ndarray, but get {type(vec)}")
        if len(vec.shape) != 1:
            raise ValueError(f"vec requires a 1-dimensional array, but get {vec.shape}")
        n_qubits = np.log2(vec.shape[0])
        if n_qubits % 1 != 0:
            raise ValueError(f"vec size {vec.shape[0]} is not power of 2")
        n_qubits = int(n_qubits)
        if self.n_qubits != n_qubits:
            raise ValueError(f"{n_qubits} qubits vec does not match with simulation qubits ({self.n_qubits})")
        self.sim.set_qs(vec / np.sqrt(np.sum(np.abs(vec)**2)))

    def get_expectation_with_grad(self,
                                  hams: Hamiltonian,
                                  circ_right: Circuit,
                                  circ_left: Circuit = None,
                                  encoder_params_name=None,
                                  ansatz_params_name=None,
                                  parallel_worker: int = None):
        r"""
        Get a function that return the forward value and gradient w.r.t circuit parameters.
        This method is designed to calculate the expectation and its gradient shown as below.

        .. math::

            E = \left<\psi\right|U_l^\dagger H U_r \left|\psi\right>

        where :math:`U_l` is circ_left, :math:`U_r` is circ_right, :math:`H` is hams
        and :math:`\left|\psi\right>` is the current quantum state of this simulator.

        Args:
            hams (Hamiltonian): The hamiltonian that need to get expectation.
            circ_right (Circuit): The :math:`U_r` circuit described above.
            circ_left (Circuit): The :math:`U_l` circuit described above. By default, this circuit
                will be none, and in this situation, :math:`U_l` will be equals to
                :math:`U_r`. Default: None.
            encoder_params_name (list[str]): To specific which parameters belongs to encoder,
                that will encoder the input data into quantum state. The encoder data
                can be a batch.
            ansatz_params_name (list[str]): To specific which parameters belongs to ansatz,
                that will be trained during training.
            parallel_worker (int): The parallel worker numbers. The parallel workers can handle
                batch in parallel threads.

        Returns:
            GradOpsWrapper, a grad ops wrapper than contains information to generate this grad ops.

        Examples:
            >>> import numpy as np
            >>> from mindquantum import Simulator, Hamiltonian
            >>> from mindquantum import Circuit
            >>> from mindquantum.core.operators import QubitOperator
            >>> circ = Circuit().ry('a', 1)
            >>> ham = Hamiltonian(QubitOperator('Z0'))
            >>> sim = Simulator('projectq', 1)
            >>> grad_ops = sim.get_expectation_with_grad(ham, circ)
            >>> grad_ops(np.array([1.0]))
            (array([[0.54030231+0.j]]), array([[[-0.84147098+0.j]]]))
        """
        if isinstance(hams, Hamiltonian):
            hams = [hams]
        elif not isinstance(hams, list):
            raise ValueError(f"hams requires a Hamiltonian or a list of Hamiltonian, but get {type(hams)}")
        for h_tmp in hams:
            if not isinstance(h_tmp, Hamiltonian):
                raise TypeError(f"hams's element should be a Hamiltonian, but get {type(h_tmp)}")
            _check_hamiltonian_qubits_number(h_tmp, self.n_qubits)
        if not isinstance(circ_right, Circuit):
            raise ValueError(f"Quantum circuit need a Circuit, but get {type(circ_right)}")
        if circ_left is not None and not isinstance(circ_left, Circuit):
            raise ValueError(f"Quantum circuit need a Circuit, but get {type(circ_left)}")
        if circ_left is None:
            circ_left = Circuit()
        if circ_left.has_measure or circ_right.has_measure:
            raise ValueError("circuit for variational algorithm cannot have measure gate")
        if parallel_worker is not None and not isinstance(parallel_worker, int):
            raise ValueError(f"parallel_worker need a integer, but get {type(parallel_worker)}")
        if encoder_params_name is None and ansatz_params_name is None:
            encoder_params_name = []
            ansatz_params_name = [i for i in circ_right.params_name]
            for i in circ_left.params_name:
                if i not in ansatz_params_name:
                    ansatz_params_name.append(i)
        if encoder_params_name is not None and not isinstance(encoder_params_name, list):
            raise ValueError(f"encoder_params_name requires a list of str, but get {type(encoder_params_name)}")
        if ansatz_params_name is not None and not isinstance(ansatz_params_name, list):
            raise ValueError(f"ansatz_params_name requires a list of str, but get {type(ansatz_params_name)}")
        if encoder_params_name is None:
            encoder_params_name = []
        if ansatz_params_name is None:
            ansatz_params_name = []
        s1 = set(circ_right.params_name) | set(circ_left.params_name)
        s2 = set(encoder_params_name) | set(ansatz_params_name)
        if s1 - s2 or s2 - s1:
            raise ValueError("encoder_params_name and ansatz_params_name are different with circuit parameters")
        circ_n_qubits = max(circ_left.n_qubits, circ_right.n_qubits)
        if self.n_qubits < circ_n_qubits:
            raise ValueError(f"Simulator has {self.n_qubits} qubits, but circuit has {circ_n_qubits} qubits.")
        version = "both"
        if not ansatz_params_name:
            version = "encoder"
        if not encoder_params_name:
            version = "ansatz"

        def grad_ops(*inputs):
            if version == "both" and len(inputs) != 2:
                raise ValueError("Need two inputs!")
            if version in ("encoder", "ansatz") and len(inputs) != 1:
                raise ValueError("Need one input!")
            if version == "both":
                _check_encoder(inputs[0], len(encoder_params_name))
                _check_ansatz(inputs[1], len(ansatz_params_name))
                batch_threads, mea_threads = _thread_balance(inputs[0].shape[0], len(hams), parallel_worker)
                inputs0 = inputs[0]
                inputs1 = inputs[1]
            if version == "encoder":
                _check_encoder(inputs[0], len(encoder_params_name))
                batch_threads, mea_threads = _thread_balance(inputs[0].shape[0], len(hams), parallel_worker)
                inputs0 = inputs[0]
                inputs1 = np.array([])
            if version == "ansatz":
                _check_ansatz(inputs[0], len(ansatz_params_name))
                batch_threads, mea_threads = _thread_balance(1, len(hams), parallel_worker)
                inputs0 = np.array([[]])
                inputs1 = inputs[0]
            if circ_left:
                f_g1_g2 = self.sim.non_hermitian_measure_with_grad([i.get_cpp_obj() for i in hams],
                                                                   [i.get_cpp_obj(hermitian=True) for i in hams],
                                                                   circ_right.get_cpp_obj(),
                                                                   circ_right.get_cpp_obj(hermitian=True),
                                                                   circ_left.get_cpp_obj(),
                                                                   circ_left.get_cpp_obj(hermitian=True), inputs0,
                                                                   inputs1, encoder_params_name, ansatz_params_name,
                                                                   batch_threads, mea_threads)
            else:
                f_g1_g2 = self.sim.hermitian_measure_with_grad([i.get_cpp_obj()
                                                                for i in hams], circ_right.get_cpp_obj(),
                                                               circ_right.get_cpp_obj(hermitian=True), inputs0, inputs1,
                                                               encoder_params_name, ansatz_params_name, batch_threads,
                                                               mea_threads)
            res = np.array(f_g1_g2)
            if version == 'both':
                f = res[:, :, 0]
                g1 = res[:, :, 1:1 + len(encoder_params_name)]
                g2 = res[:, :, 1 + len(encoder_params_name):]
                return f, g1, g2
            f = res[:, :, 0]
            g = res[:, :, 1:]
            return f, g

        grad_wrapper = GradOpsWrapper(grad_ops, hams, circ_right, circ_left, encoder_params_name, ansatz_params_name,
                                      parallel_worker)
        s = f'{self.n_qubits} qubit' + ('' if self.n_qubits == 1 else 's')
        s += f' {self.backend} VQA Operator'
        grad_wrapper.set_str(s)
        return grad_wrapper


def _check_encoder(data, encoder_params_size):
    if not isinstance(data, np.ndarray):
        raise ValueError(f"encoder parameters need numpy array, but get {type(data)}")
    data_shape = data.shape
    if len(data_shape) != 2:
        raise ValueError("encoder data requires a two dimension numpy array")
    if data_shape[1] != encoder_params_size:
        raise ValueError(f"encoder parameters size do not match with encoder parameters name,\
need {encoder_params_size} but get {data_shape[1]}.")


def _check_ansatz(data, ansatz_params_size):
    """check ansatz"""
    if not isinstance(data, np.ndarray):
        raise ValueError(f"ansatz parameters need numpy array, but get {type(data)}")
    data_shape = data.shape
    if len(data_shape) != 1:
        raise ValueError("ansatz data requires a one dimension numpy array")
    if data_shape[0] != ansatz_params_size:
        raise ValueError(f"ansatz parameters size do not match with ansatz parameters name,\
need {ansatz_params_size} but get {data_shape[0]}")


def _thread_balance(n_prs, n_meas, parallel_worker):
    """threa balance"""
    if parallel_worker is None:
        parallel_worker = n_meas * n_prs
    if n_meas * n_prs <= parallel_worker:
        batch_threads = n_prs
        mea_threads = n_meas
    else:
        if n_meas < n_prs:
            batch_threads = min(n_prs, parallel_worker)
            mea_threads = min(n_meas, max(1, parallel_worker // batch_threads))
        else:
            mea_threads = min(n_meas, parallel_worker)
            batch_threads = min(n_prs, max(1, parallel_worker // mea_threads))
    return batch_threads, mea_threads


def _check_hamiltonian_qubits_number(hamiltonian, sim_qubits):
    """check hamiltonian qubits number"""
    if hamiltonian.how_to != MODE['origin']:
        if hamiltonian.n_qubits != sim_qubits:
            raise ValueError(f"Hamiltonian qubits is {hamiltonian.n_qubits}, not match \
with simulator qubits number {sim_qubits}")
    else:
        if hamiltonian.n_qubits > sim_qubits:
            raise ValueError(f"Hamiltonian qubits is {hamiltonian.n_qubits}, which is bigger than simulator qubits.")


class GradOpsWrapper:
    """
    Wrapper the gradient operator that with the information that generate this
    gradient operator.

    Args:
        grad_ops (Union[FunctionType, MethodType])): A function or a method
            that return forward value and gradient w.r.t parameters.
        hams (Hamiltonian): The hamiltonian that generate this grad ops.
        circ_right (Circuit): The right circuit that generate this grad ops.
        circ_left (Circuit): The left circuit that generate this grad ops.
        encoder_params_name (list[str]): The encoder parameters name.
        ansatz_params_name (list[str]): The ansatz parameters name.
        parallel_worker (int): The number of parallel worker to run the batch.
    """
    def __init__(self, grad_ops, hams, circ_right, circ_left, encoder_params_name, ansatz_params_name, parallel_worker):
        self.grad_ops = grad_ops
        self.hams = hams
        self.circ_right = circ_right
        self.circ_left = circ_left
        self.encoder_params_name = encoder_params_name
        self.ansatz_params_name = ansatz_params_name
        self.parallel_worker = parallel_worker
        self.str = ''

    def __call__(self, *args):
        return self.grad_ops(*args)

    def set_str(self, s):
        """Set expression for gradient operator."""
        self.str = s


__all__ = ['Simulator', 'get_supported_simulator', 'GradOpsWrapper']
