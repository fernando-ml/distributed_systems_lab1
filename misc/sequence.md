git clone https://github.com/fernando-ml/distributed_systems_lab1.git -b main

cd distributed_systems_lab1/

bash start_lab1.sh "10.128.0.2" "round_robin_lb"
this takes apprx. 120.88 seconds

bash start_lab1.sh "10.128.0.2" "weighted_lb"
120.14 seconds