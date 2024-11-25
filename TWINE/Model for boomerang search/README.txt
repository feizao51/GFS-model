For example to reproduce our distinguisher for 14 rounds of TWINE, you can use the following command:

```
python3 boom.py -r0 4 -rm 7 -r1 3 -w0 6 -wDDT 1 -wFBCT 2 -wDDT2 4 -w1 6
```

Running this command, leaves a `.txt` file named `result_4_7_3.txt` within the working directory.