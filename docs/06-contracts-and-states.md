# 现行契约与交付状态

稿件、来源索引、账本和片段继续采用 JSON v1；models.py 的 validate_*_v1 检查现行传输格式。CaseManifest/Fact/Requirement 等 dataclass 是扩展 DTO，不替代全部现行序列化。

新增可选 case_id/document_id：分别标识同一材料项目与其文档。prepare 为软著 case 生成持久标识，源码和手册使用不同 document_id；draft/audit/hash/build_id 仍独立，不能把一份文档的审阅套用到另一份。旧 v1 未携带标识的案例仍兼容。

通用持久状态：blocked（构建前拒绝）、failed（制作/检查失败）、draft（未完成审阅或明确草稿）、awaiting-review、reviewed。`business-pending` 是内部状态：共享制作成功后须绑定业务原件及校验审计，才可进入 awaiting-review；不能直接 review-init/finalize。

copyright package 包含两份独立子交付。正式准备包只有在两个子文档分别真实审阅、源码/手册/填写辅助及审阅记录哈希完整时才能 package-finalize。此状态不表示已提交或具备登记资格。

明确 preview 用途可将权属/完成日期等缺口列为待确认，不能放宽源码哈希、选段、软件名称/版本和手册来源检查。子文档强制 draft，根包 purpose=preview；现有 review-init 和 package-finalize 都拒绝把它升级。确认字段后须重新构建正式准备包。

业务原件、来源、模板、辅助文件、子文档、审阅或生成器变化应使对应旧证据失效。旧产物不原地覆盖；哈希证明身份一致，不能证明语义或权属。

## 图文手册扩展

v1稿件新增可选image块：text为图注、path为case内PNG/JPEG、sha256为原件哈希；图片复制到审计并参与构建身份，旧paragraph/table/code保持兼容。图注需要证据引用，图片语义仍需审阅。段落可携带heading_level或monospace以保留手册结构。copyright软件身份由业务校验后投影到页眉，未知权属不写入技术手册正文。
