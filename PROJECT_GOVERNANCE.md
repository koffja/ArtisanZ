# ArtisanZ 项目治理与同步说明

本文档记录 ArtisanZ 项目的由来、分支规划、官方同步流程，以及后续开发和 AI agents 参与修改时必须遵守的规则。

## 1. 项目背景

ArtisanZ 是基于官方 Artisan 项目的个人定制版本。

- 官方仓库：`https://github.com/artisan-roaster-scope/artisan`
- 个人 fork：`git@github.com:koffja/ArtisanZ.git`
- 本地正式工作目录：`/Users/chengzhe/Projects/ArtisanZ`

此前曾存在旧的 `ZHES-Artisan` 仓库和一个本地快照式修改目录，但为了避免历史混乱，现已重新从 GitHub 直接 fork 官方 Artisan 到 `koffja/ArtisanZ`，并以该仓库作为唯一长期维护仓库。

## 2. 核心目标

ArtisanZ 的长期目标是：

1. 保持与官方 Artisan 的 git 历史关联，方便随时合并官方更新。
2. 保持个人定制功能独立，不向官方提交 PR。
3. 所有个人功能、构建脚本、中文定制和业务逻辑都维护在 `ArtisanZ` 分支。
4. 官方同步基线与个人开发分支分离，降低合并冲突和误推风险。

## 3. 分支规划

### `master`

`master` 是官方同步基线分支。

规则：

- 只用于同步官方 `upstream/master`。
- 不在 `master` 上做个人功能开发。
- 不在 `master` 上修补 ArtisanZ 自定义功能。
- 不把旧本地快照历史、实验提交或个人功能直接提交到 `master`。

### `ArtisanZ`

`ArtisanZ` 是个人定制主分支，也是 GitHub 仓库默认分支。

规则：

- 所有个人修改都在 `ArtisanZ` 分支进行。
- 自定义功能、便携打包脚本、中文文档、中文翻译、自定义测试等都属于 `ArtisanZ` 分支内容。
- 每次官方更新后，从 `master` 合并到 `ArtisanZ`，再修补冲突。
- 后续 AI agents 修改代码时，默认只允许在 `ArtisanZ` 分支工作。

## 4. 当前自定义功能范围

目前从旧本地项目迁移到 `ArtisanZ` 的自定义内容主要包括：

- 投豆目标管理功能：
  - `src/artisanlib/charge_manager.py`
  - `src/artisanlib/charge_dialog.py`
  - `src/test/unitary/artisanlib/test_charge_manager.py`
- 主程序集成：
  - `src/artisanlib/main.py`
  - `src/artisanlib/canvas.py`
- 中文翻译定制：
  - `src/translations/artisan_zh_CN.ts`
  - `src/translations/artisan_zh_CN.qm`
- Windows 便携打包相关：
  - `build-win-portable.bat`
  - `PORTABLE_BUILD_GUIDE.md`
  - `artisan打包win说明.txt`
- 功能说明与规划：
  - `CHARGE_TARGET_SUMMARY.md`
  - `charge_target_plan.md`

## 5. 推荐日常开发流程

进入正式工作目录：

```bash
cd /Users/chengzhe/Projects/ArtisanZ
git checkout ArtisanZ
```

开发个人功能：

```bash
git checkout ArtisanZ
# 修改代码
git status
git add -A
git commit -m "feat: describe ArtisanZ customization"
git push origin ArtisanZ
```

如果是较大功能，可从 `ArtisanZ` 再开 feature 分支：

```bash
git checkout ArtisanZ
git checkout -b feature/some-artisanz-feature
# 修改、测试、提交
git checkout ArtisanZ
git merge feature/some-artisanz-feature
git push origin ArtisanZ
```

## 6. 同步官方 Artisan 更新流程

当官方 Artisan 有新版本或新提交时，按以下步骤操作。

### 第一步：更新官方基线 `master`

```bash
cd /Users/chengzhe/Projects/ArtisanZ
git checkout master
git fetch upstream
git merge upstream/master
git push origin master
```

### 第二步：把官方更新合并到个人分支 `ArtisanZ`

```bash
git checkout ArtisanZ
git merge master
```

如果出现冲突，优先原则如下：

1. 保留官方新增功能和 bug fixes。
2. 保留 ArtisanZ 自定义功能。
3. 不要用旧版大文件直接覆盖新版官方文件，尤其是：
   - `src/artisanlib/main.py`
   - `src/artisanlib/canvas.py`
   - `src/translations/artisan_zh_CN.ts`
4. 对核心文件冲突，优先做最小补丁迁移，而不是整文件替换。

解决冲突后：

```bash
git status
git add -A
git commit
git push origin ArtisanZ
```

## 7. 重要原则：不要污染官方基线

禁止做以下事情：

- 不要在 `master` 上提交 ArtisanZ 自定义功能。
- 不要把旧仓库的本地历史整体推入 `ArtisanZ`。
- 不要把 `upstream-update`、`backup-before-upstream-merge` 等旧本地分支推到新 fork。
- 不要 force push `master`，除非明确知道是在重置为官方 `upstream/master` 且已经确认无自定义提交。
- 不要把 `origin` 指回旧仓库或已删除仓库。

## 8. 当前远程配置应为

```bash
origin   git@github.com:koffja/ArtisanZ.git
upstream https://github.com/artisan-roaster-scope/artisan.git
```

可用以下命令检查：

```bash
git remote -v
git branch --show-current
git status
```

## 9. AI agents 修改前检查清单

任何 AI agent 修改本项目之前，必须先确认：

```bash
git branch --show-current
git status --short
git remote -v
```

要求：

- 当前分支应为 `ArtisanZ`，除非任务明确是同步官方 `master`。
- 工作区必须清楚当前已有未提交变更，不能覆盖用户改动。
- 修改前先理解官方同步关系和本文件规划。

## 10. 验证建议

常用验证命令：

```bash
cd src
python3 -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

如果本机缺少 pytest 或 PyQt 依赖，应先安装项目依赖：

```bash
cd src
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 11. 一句话规则

`master` 跟官方走，`ArtisanZ` 做个人产品；官方更新先进入 `master`，再合并到 `ArtisanZ`，所有自定义修补只发生在 `ArtisanZ`。
