For example to reproduce our distinguisher for 14 rounds of WARP, you can use the following command:

```sh
python3 boom.py -r0 2 -rm 10 -r1 2 -w0 6 -wDDT 1 -wFBCT 1.5 -wDDT2 2 -w1 6
```

Running this command, leaves a `.txt` file named `result_2_10_2.txt` within the working directory.