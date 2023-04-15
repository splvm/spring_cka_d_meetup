# Networking Lab2

## 1. Preparing

Before moving forward, you need to have a cluster either in local or in a public cloud. The lab is based on the Chapter 11 from the book [Kubernetes in Action](https://www.manning.com/books/kubernetes-in-action). If you are using Minikube, the load balancer may not work.

**Useful tools**:

- [kubens](https://github.com/ahmetb/kubectx)
- [kubectl-node-shell](https://github.com/kvaps/kubectl-node-shell)

**Code Resource**:

- [Kubernetes in Action, 2nd edition, Chapter11](https://github.com/luksa/kubernetes-in-action-2nd-edition/tree/master/Chapter11)

### Cluster Preparation

| Command                                                                                                                                                                                      | Description                                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `az group create -n k8sLearn -l westus3`                                                                                                                                                     | Create a resource group.                                                  |
| `az aks create -g k8sLearn -n netDemo --node-count 2 --node-vm-size standard_d2a_v4 --enable-addons monitoring --enable-msi-auth-for-monitoring --generate-ssh-keys --enable-node-public-ip` | Create a cluster with public ip enabled                                   |
| `kubens`                                                                                                                                                                                     | Make sure you are in the default namespace.                               |
| `kubectl apply -f SETUP/ --recursive`                                                                                                                                                        | Create pods for the lab.                                                  |
| `kubectl get pods`                                                                                                                                                                           | Check the pods.                                                           |
| `kubectl apply labs/networking2/quote-svc.yaml`                                                                                                                                              | Create a service for the quote pod.                                       |
| `kubectl get svc`                                                                                                                                                                            | Check the services.                                                       |
| `kubectl node-shell <node-name>`                                                                                                                                                             | Connect to the node.                                                      |
| `curl <svc-ip>:<svc-port>`                                                                                                                                                                   | Check the service.                                                        |
| `kubectl run mycurlpod --image=curlimages/curl -i --tty -- sh`                                                                                                                               | Create a pod with curl image and execute into it.                         |
| `curl http://quote`                                                                                                                                                                          | Check the service.                                                        |
| `curl http://quote.default`<br/> `curl http://quote.default.svc`<br/> `curl http://quote.default.svc.cluster`<br/> `curl http://quote.default.svc.cluster.local`                             | Valid commands.                                                           |
| `kubectl node-shell <node-name>`                                                                                                                                                             | Connect to the node.                                                      |
| `iptables -L -t nat \| grep <quote-svc-ip>`                                                                                                                                                  | Check the NAT rule for the service.                                       |
| `kubectl node-shell <another-node-name>`                                                                                                                                                     | Connect to the other node.                                                |
| `iptables -L -t nat \| grep <quote-svc-ip>`                                                                                                                                                  | Check the NAT rule for the service.                                       |
| `kubectl expose pod quiz --name quiz`                                                                                                                                                        | Create a service for the quiz pod.                                        |
| `kubectl get svc -o wide`                                                                                                                                                                    | Check the services.                                                       |
| `kubectl delete pod mycurlpod`                                                                                                                                                               | Delete the pod.                                                           |
| `kubectl run mycurlpod --image=curlimages/curl -i --tty -- sh`                                                                                                                               | Create a pod with curl image and execute into it.                         |
| `kubectl exec mycurlpod -i --tty -- sh`                                                                                                                                                      | Execute into the pod.                                                     |
| `printenv`                                                                                                                                                                                   | Check the environment variables in a pod to find the services we created. |
| `curl <env-variable>`                                                                                                                                                                        | Check the service using environment variable.                             |
| `kubectl apply -f labs/networking-2/kiada-stable-and-canary.yaml`                                                                                                                            | Create a deployment for kiada.                                            |
| `kubectl apply -f labs/networking-2/kiada-svc-nodeport.yaml`                                                                                                                                 | Create a service for kiada.                                               |
| `kubectl get pods -w`                                                                                                                                                                        | Check the pods.                                                           |
| `kubectl port-forward kiada-001 8080`                                                                                                                                                        | Forward the port 8080 to the pod.                                         |
| `curl localhost:8080`                                                                                                                                                                        | Check the service.                                                        |
| `kubectl apply -f labs/networking-2/kiada-svc-nodeport.yaml`                                                                                                                                 | Create a service with type nodeport for kiada.                            |
| `k apply -f labs/networking-2/kiada-svc-lb.yaml`                                                                                                                                             | Create a service with type load balancer for kiada.                       |
