#python3 process_A.py -cn conf/conf-dben.json
#python3 process_B.py -cn conf/conf-dben.json
#python3 learn.py P -cn conf/conf-dben.json
#python3 learn.py N -cn conf/conf-dben.json
python3 filter.py -i ../input/real.tsv -o ../output/real -cn conf/conf-dben.json
python3 filter.py -i ../input/synt.tsv -o ../output/synt -cn conf/conf-dben.json