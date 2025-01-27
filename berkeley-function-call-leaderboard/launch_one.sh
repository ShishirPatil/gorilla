#rm -rf score
#rm -rf result

killall /home/ubuntu/miniconda3/envs/BFCL2/bin/python
wait 1
#bfcl generate --test-category=simple,parallel,multiple,parallel_multiple --model="$1" --num-gpus=4 --backend=sglang
#bfcl evaluate --test-category=simple,parallel,multiple,parallel_multiple --model="$1"
#bfcl generate --test-category=parallel_multiple --model="$1" --num-gpus=4 --backend=sglang
#bfcl evaluate --test-category=parallel_multiple --model="$1"
bfcl generate --test-category=exec_simple --model="$1" --num-gpus=4 --backend=sglang
bfcl evaluate --test-category=exec_simple --model="$1"

