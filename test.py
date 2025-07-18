import docker
import time

o_docker = docker.from_env()





all_containers = o_docker.containers.list(all=True)
for container in all_containers:
    print(container.status)
    print (container)
    print(container.name)
    print(container.id)

    for label in container.labels:
        if label == 'infradmin.is_bdd' and container.labels[label] == 'true':
            print(f"{container.name} is a database because Label is : {label} value is : {container.labels[label]} ")
    volumes = container.attrs['Mounts']
    print(f"Volumes for {container.name} are :")
    for volume in volumes:
        print(f"source is : {volume['Source']} and destination is : {volume['Destination']}")

l_volumes = o_docker.containers.get("opensearch").attrs['HostConfig']['Binds']
for s_volume in l_volumes:
    print(s_volume)
    source = s_volume.split(':')[0]
    destination = s_volume.split(':')[1]
    
    print(f"sourc is : {source.replace('/home/hcastellaville/', '/usr/src/app/infradmin/data/')} and destination is : {s_volume.split(':')[1]}")
    
list1 = [1, 2, 3]
list2 = [4, 5, 6]

print(list1 + list2)



start_time = time.time().strftime('%Y-%m-%d')
print(start_time + "backup")