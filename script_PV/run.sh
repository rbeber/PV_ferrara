# run: horizon >> rSun >> rSun_month >> mosaic
#
python3 generateHorizonGrass.py && \
python3 generateRsunParallel.py --dataFolder /root/PV_ferrara/FE_data/output --outFolder /root/PV_ferrara/FE_data/output/rSun --horizon_step 10 && \
python3 generate_Rsun_MonthMaps.py --dataFolder /root/PV_ferrara/FE_data/output --outFolder /root/PV_ferrara/FE_data/output/rSun_sum --process rsun_month --dataset_nr 0 && \
python3 generate_mosaic4months.py
