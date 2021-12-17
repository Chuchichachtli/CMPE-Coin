# cmpecoin-team-5
cmpecoin-team-5 created by GitHub Classroom

# Before run

## Install dependencies

```
pip3 install -r requirements.txt
```

## prepare the key file

```
python3 keyGenerator.py
```

# How to run

Run this command to execute blockchain system with 9 processes. This will create 1 dispatcher node, 3 validator and simple nodes, 1 logger node and 1 transaction server node.

```
mpiexec -n 9 python3 main.py
```

If that does not work try the following command

```
mpiexec -n 9 --use-hwthread-cpus python3 main.py
```

Run these commands to start client application

```
cd client
yarn install
yarn start
```
