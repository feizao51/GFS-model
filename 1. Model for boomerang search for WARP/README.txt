For example to reproduce our distinguisher for 14 rounds of WARP, you can use the following command:

```sh
python3 boom.py -r0 2 -rm 10 -r1 2 -w0 6 -wDDT 2 -wFBCT 3 -wDDT2 4 -w1 6
```

Running this command, leaves a `.txt` file named `result_2_10_2.txt` within the working directory.