# Networking Lab 3

## 1. Preparing Reading
- [Kubernetes in Action 2nd Chapter12](https://www.manning.com/books/kubernetes-in-action-second-edition)
- [Layer 4 VS Layer 7 Load Balancer](https://www.youtube.com/watch?v=aKMLgFVxZYk&ab_channel=HusseinNasser)
- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Create an ingress controller in Azure Kubernetes Service (AKS)](https://learn.microsoft.com/en-us/azure/aks/ingress-basic?tabs=azure-cli)

## 2. Source Code Preparation
- [Source code](https://github.com/luksa/kubernetes-in-action-2nd-edition/tree/master/Chapter12)
  - Please clone the repo and go to the Chapter12 folder.

## 3. Cluster Preparation & Lab

Please run the following commands to install a ingress controller in your cluster before moving forward. The cluster should be clean before installing the ingress controller.
```bash
NAMESPACE=ingress-basic

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --create-namespace \
  --namespace $NAMESPACE \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
```

| Command | Execution Place | Description |
| ------- | --------------- | ----------- |
| `kubectl run -it --rm dns-test --image=giantswarm/tiny-tools` | Host | Create a pod with dns tools |
| `nslookup quote` | Pod: dns-test | Check the quote service |
| `nslookup kiada` | Pod: dns-test | Check the quote service |
| `kubectl get svc kiada` | Pod: dns-test | Check the kiada service: it has cluster-ip and external-ip, but nslookup only return cluster-ip |
| `nslookup -query=SRV kiada` | Pod: dns-test | Check the SRV record for kiada service |
| `kubectl apply -f SETUP/ --recursive` | Host | Create the services and pods |
| `kubectl get svc` | Host | Check the services |
| `k apply -f ing.kiada-example-com.yaml` | Host | Create the ingress |


The following commands should be cleaned before publishing the lab.
- `k edit ingress` 
  - Add the following content
    ```yaml
    ...
    metadata:
      annotations:
        kubernetes.io/ingress.class: nginx
    ...
    spec:
      ingressClassName: nginx
    ...
    ```
- `kubectl get ing kiada-example-com -o yaml`
  - Check the ingress yaml file and you should see the follwoing content
    ```yaml
    ...
    status:
      loadBalancer:
        ingress:
        - ip: 20.106.111.159 # Your ip here should be different
    ```
- `sudo vim /etc/hosts`
  - Add the following content to the `hosts` file and make sure the changes has been saved successfully.
    ```bash
    20.106.111.159      kiada.example.com
    ```
- `curl --resolve kiada.example.com:80:20.106.111.159 http://kiada.example
.com -v`
  - You cannot ping the ingress load balancer ip or simply send an HTTP request.
- `kubectl apply -f ing.api-example-com.yaml`
  - Create the ingress for api service (quote service and quiz service)
  - `sudo vim /etc/hosts`
    - Add the following content to the `hosts` file and make sure the changes has been saved successfully.
    ```bash
    20.106.111.159      kiada.example.com api.example.com
    ```
  - `curl api.example.com/quote`
    - You should see the quote service response.




What is a SRV record in DNS?
SRV (Service) record is a type of DNS record used to specify the location of a service available in a domain. It allows services like SIP, XMPP, LDAP, and others to be discovered automatically by clients. The SRV record contains information such as the hostname and port number of the server providing the service, as well as the priority and weight of the server in relation to other servers providing the same service. This information is used by clients to connect to the appropriate server for the desired service.
