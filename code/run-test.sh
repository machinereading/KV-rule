python3 process_A.py -cn conf/conf-test.json
python3 process_B.py -cn conf/conf-test.json
python3 learn.py P -cn conf/conf-test.json
python3 learn.py N -cn conf/conf-test.json
python3 filter.py -i ../input/ours.tsv -o ../output/test -cn conf/conf-test.json