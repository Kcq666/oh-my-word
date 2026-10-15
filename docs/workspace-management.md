# 工作区管理

开发工作区和发布检出承担不同职责：开发工作区保存持续修改，发布检出只用于验证一个明确的提交。发布检出可以是临时目录，但不能作为长期状态记录的事实源。

## 开始工作前

在开发工作区记录以下三项身份：

```powershell
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

如果工作区没有 Git 元数据，先初始化本地 `main`，绑定已有远端，再核对工作树是否有未提交改动。已有改动应保留并逐项审阅；不要用远端提交号代替工作树身份。

## 发布前

发布验证必须从明确的提交创建干净检出，并记录：

- 开发工作区的提交、工作树状态和未提交文件；
- 发布检出的提交、远端分支指向和工作树状态；
- 两个目录的用途，以及哪些证据只适用于其中一个目录。

本地代码清单用 `python tools/check_code_manifest.py` 校验。首次用 `--refresh --include <相对路径>` 创建清单，后续用 `--refresh` 更新哈希；新增文件必须显式用 `--include` 纳入。完整依赖验收用 `python tools/check_full_dependencies.py`，它通过 pytest 运行全部测试并记录解释器、依赖版本、测试总数与结果，出现 skip、xfail 或 xpass 均失败。
