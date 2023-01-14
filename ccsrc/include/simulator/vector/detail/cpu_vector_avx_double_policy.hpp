//   Copyright 2022 <Huawei Technologies Co., Ltd>
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.
#ifndef INCLUDE_VECTOR_DETAIL_CPU_VECTOR_AVX_DOUBLE_POLICY_HPP
#define INCLUDE_VECTOR_DETAIL_CPU_VECTOR_AVX_DOUBLE_POLICY_HPP
#include "simulator/vector/detail/cpu_vector_policy.hpp"

namespace mindquantum::sim::vector::detail {
struct CPUVectorPolicyAvxDouble : public CPUVectorPolicyBase<CPUVectorPolicyAvxDouble, double> {
    void ApplySingleQubitMatrix(qs_data_p_t src, qs_data_p_t des, qbit_t obj_qubit, const qbits_t& ctrls,
                                const std::vector<std::vector<py_qs_data_t>>& m, index_t dim);
};
}  // namespace mindquantum::sim::vector::detail
#endif
