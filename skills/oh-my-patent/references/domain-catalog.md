# 子 Skill 目录

可执行登记以 [registry.yaml](../domains/registry.yaml) 为准，记录维护人、版本、范围、排除条件、复核日、状态与质量证据；`python tools/patent_lab.py modules` 校验。六个模块当前均为 experimental，不凭结构通过改为 validated。

版本：1.0；维护日：2026-10-13。按技术贡献和保护主题选择，非行业关键词分类器。所有路径相对于本目录文件，保留整个仓库结构可直接读取。主入口是 [oh-my-patent](../SKILL.md)。

| ID / 子 Skill | 选择依据 | 易混淆边界 |
| --- | --- | --- |
| [patent-software-ai](../domains/patent-software-ai/SKILL.md) | 数据处理、算法、软件控制、模型构建/训练/应用是技术贡献 | 公司属于互联网或机械设备提到软件，不足以触发 |
| [patent-mechanical](../domains/patent-mechanical/SKILL.md) | 部件结构、空间/连接关系、运动或制造装配是技术贡献 | 新材料配方本身不因用于机械而成为结构发明 |
| [patent-electronics](../domains/patent-electronics/SKILL.md) | 电路拓扑、信号、通信协议、器件或电子控制链路有改进 | 仅使用通用计算机执行算法通常由软件模块处理 |
| [patent-chemical-materials](../domains/patent-chemical-materials/SKILL.md) | 化学物质、组合物、配方、材料结构或制备过程有改进 | 工业领域算法只有涉及具体材料约束/性能披露时才组合本模块 |
| [patent-biomedical](../domains/patent-biomedical/SKILL.md) | 生物材料、序列、药物、医学检测或医疗技术关联保护客体/实施条件 | 医疗产品名称本身不意味着需要药物或序列表流程 |
| [patent-design](../domains/patent-design/SKILL.md) | 外观设计的视图、保护部分、简要说明与 GUI 状态 | 属文书类型模块；不生成技术权利要求，也不以技术性能界定外观保护 |

前五项为宽领域起始模块，第六项为外观文书模块，均为初版撰写/审查指导，未进行生成质量盲测。它们不是完整行业列表；农业、能源、土木等按实际手段组合，确有独特披露要求再扩展。IPC/CPC 可辅助检索和复核，不能作为一对一 Skill 路由规则。

无匹配：保留通用路径，列出缺少的领域指导和应补材料，不套用最近名称。跨领域：指定主贡献及辅助领域，处理接口和冲突；不因组合而复制账本、实验或权利要求。

新增模块遵循 [子 Skill 契约](domain-skill-contract.md)，登记路径、触发/排除依据及版本，加入正例、易混淆反例和交叉领域评测。嵌套 Skill 未经宿主安装和触发验证时，只能声称“入口可按路径加载”；子目录单独复制将失去共用引用。
