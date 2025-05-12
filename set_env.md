# NK25-SCWarn

原SCWarn发表于2021年，使用python3.7版本的依赖包。

我们的复现使用python3.11，并对应更新安装包，经测试可以正确运行。

## 虚拟环境配置流程

创建conda环境

```
conda create -n scwarn python=3.11
```

激活环境
```
conda activate scwarn
```

安装 SCWarn 官方给出的依赖
```
pip install -r requirements.txt
```

P.S. 或直接安装我们检验过的 python3.11 对应依赖
```
pip install -r requirements_py311.txt
```

## 依赖包版本对应
注意：>= 右侧对应的版本号，就是实际的版本
```
numpy >= 2.1.3
matplotlib >= 3.10.3
pandas >= 2.2.3
tensorflow >= 2.19.0
torch >= 2.7.0
PyYAML >= 6.0.2
scikit_learn >= 1.6.1
statsmodels >= 0.14.4
tqdm >= 4.67.1
```
