projects=(
  "stream-processor"
  "campaign-scheduler"
)

for project in "${projects[@]}"
do
  out="./${project}/pb"
  mkdir -p ${out} &&
  python -m grpc_tools.protoc -I ./protos --python_out=${out} --pyi_out=${out} --grpc_python_out=${out} ./protos/*
done
