#! /bin/sh
# @auth James Lui james.lui@nasa.gov
# @contact Robert Field robert.field@columbia.edu

# Batch convert csv files into format the FWI scripts can read

if [ $# -ne 5 ]; then
  echo "Required arguments needed: 5, provided: $#"
  echo "<csv of sites> <directory of wx data> <year start> <year end> <output directory>"
  exit 1
fi

listfiles=$1
indir=$2
yearstart=$3
yearend=$4
outdir=$5

# Filter bounding box for Canada (but also include stuff on different latitudes)
lonmin=-140
lonmax=-50

bash_source=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P)
mkdir -p $outdir

# Loop over file containing details for each weather station and lat/lon coordinates
while IFS=$',' read -r -a args; do
  wmoid=${args[0]}
  wmoname=${args[1]}
  lat=${args[2]}
  lon=${args[3]}
  #echo "${indir}/${wmoid}.hourlyWxRawISD.csv"
  if [ -f "${indir}/${wmoid}.hourlyWxRawISD.csv" ] && (( $(echo "$lon > $lonmin" | bc) )) && (( $(echo "$lon < $lonmax" | bc) )) ; then
    # use wx_convert_filter.sh to do conversion
    echo ${wmoid}: $wmoname, $lat, $lon
    $bash_source/wx_convert_filter.sh "${indir}/${wmoid}.hourlyWxRawISD.csv" $yearstart $yearend $wmoid $lat $lon "${outdir}/wx_${wmoid}.csv"
  fi
done < $listfiles
