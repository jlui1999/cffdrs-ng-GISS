#! /bin/sh

listfiles=$1
indir=$2
yearstart=$3
yearend=$4
outdir=$5

# Filter bounding box for Canada (but also include stuff outside)
lonmin=-140
lonmax=-50

bash_source=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P)
mkdir -p $outdir

while IFS=$',' read -r -a args; do
  wmoid=${args[0]}
  wmoname=${args[1]}
  lat=${args[2]}
  lon=${args[3]}
  #echo "${indir}/${wmoid}.hourlyWxRawISD.csv"
  if [ -f "${indir}/${wmoid}.hourlyWxRawISD.csv" ] && (( $(echo "$lon > $lonmin" | bc) )) && (( $(echo "$lon < $lonmax" | bc) )) ; then
    # ./wx_convert_filter.sh /explore/dataportal/dataportal01/globalfwi/StnFWI/Wx/725030-14732.hourlyWxRawISD.csv 2025 2025 DUMMY 10 10 temp.csv
    echo $wmoname, $lat, $lon
    $bash_source/wx_convert_filter.sh "${indir}/${wmoid}.hourlyWxRawISD.csv" $yearstart $yearend $wmoid $lat $lon "${outdir}/wx_${wmoid}.csv"
  fi
done < $listfiles
