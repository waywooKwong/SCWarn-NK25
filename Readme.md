# Repo SCWarn 25 Nankai Test

SCWarn can identify bad software changes in online service systems.

Our repo fork: https://github.com/FSEwork/SCWarn

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

原SCWarn发表于2021年，使用python3.7版本的依赖包。

我们的复现使用python3.11，并对应更新安装包，经测试可以正确运行。

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


## Usage

**Step1: prepare for your data**

You need to transform your own data to csv format. And there must be a timestamp column in your training and testing data. 

**Step 2:  chagne the "config.yml"**

You may need to change the "train_path", "test_path" and "output_path" for your task.

And you can change the parameters in config.yml to confiure the algorithms  used by SCWarn. 

The meaning of the parameters is as follows:

- **train_path**: the path of your training dataset. In SCWarn, you need to provide with dataset in CSV format.

- **test_path**: the path of your testing dataset. In SCWarn, you need to provide with dataset in CSV format.

- **output_path**: the path of SCWarn output. SCWarn gives the anomaly score of testing data stored in a CSV format file.

- **scaler**: 'standard' or 'minmax'. Choose a scaler to preprocess the data. The 'standard' scaler will normalize the data. And the 'minmax' scaler will scale the data to the range between zero to one.

- **dim(optional)**: dimensions of the data fed SCWarn. For example, "from 1 to 7" means that SCWarn will use the 1st to 7th columns of training and testing CSV data. (PS: the 0th column is timestamp). If 'config.yml' does not include the 'dim' parameter, SCWarn will use all the columns in CSV data.

- **algorithms**: Here, you can configure the algorithms used by SCWarn.

- - **LSTM**:

  - - **epoch**: total training epoch number.
    - **batch_size**: training batch size.
    - **learning_rate**: learning rate of the optimizer in SCWarn.
    - **model_path(optional)**: the path of an existing model. If 'LSTM' includes model_path, SCWarn will use the current model to test and not train a new model. 
    - **seq_len**: The sliding window size.

  - **ISST**: ISST can only handle one single metric.

  - - **dim_pos**: ISST can only handle one metric, so we need to select a column to feed ISST. Setting dim_pos to n means that ISST uses the nth column to train and test.

  - **AE**: Autoencoder, the configuration is the same as LSTM.

  - **VAE**: Variational Autoencoder, the configuration is the same as LSTM.

  - **GRU**: the configuration is the same as LSTM.

  - **MLSTM**: Multimodal-LSTM

  - - **modal**: The modal is a list that has two int elements. The first element is the number of the first modal(begin from the 1st column). The second element is the number of the 2nd modal.
    - The rest parameters are the same as LSTM.

  - **MMAE**: Multimodal-AE, the configuration is the same as LSTM.

```yml
train_path: "data/sample/train.csv"
test_path: "data/sample/abnormal.csv"
output_path: "result/sample.csv"

scaler: 'standard'

# select dimensions used to train and test
dim:
   from: 1
   to: 4

algorithms:
  LSTM:
      epoch: 10
      batch_size: 32
      learning_rate: 0.01 
      seq_len: 10

 ISST:
     dim_pos: 3

 AE:
     epoch: 50
     batch_size: 32
     learning_rate: 0.01
     seq_len: 10

 VAE:
     epoch: 10
     batch_size: 32
     learning_rate: 0.01
     seq_len: 10

 MLSTM:
     epoch: 10
     batch_size: 32
     learning_rate: 0.01
     seq_len: 10
     modal:
       - 4 
       - 3

 MMAE:
     epoch: 10
     batch_size: 32
     learning_rate: 0.01
     seq_len: 15
     modal:
       - 4
       - 3

```

**Step 3: run SCWarn**

set service name

```shell
dataset_name: "hotel-res"

train_path: "./data/hotel-res/train/"
```

Run the command below.

```shell
python main.py
```

And then check the result_path, you will get the anomlay scores for each sample in your testing data.

## Our Usage

1. config.yaml 设置数据集名称 dataset_name: xxx
2. 运行函数
  ```
  python main.py
  ```
注意：调整一下，test_data是用 abnormal? abnormal_processed? train?

3. 绘制 result 结果图
  ```
  cd result
  设置参数 csv_folder = "xxx(dataset)"
  python plot_data.py
  ```
