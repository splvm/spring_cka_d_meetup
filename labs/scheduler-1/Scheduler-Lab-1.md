# Scheduler Lab1

## 1. Control Plane Components

### 1.1 Kubernetes Cluster Components
- Overview
  ![K8s Cluster Components](https://d33wubrfki0l68.cloudfront.net/2475489eaf20163ec0f54ddc1d92aa8d4c87c96b/e7c81/images/docs/components-of-kubernetes.svg)
- Control Plane Components
  The control plane's components make global decision about the cluster. Examples of the decisions are scheduling new pods and scaling the number of pods in a deployment to satisfy the replicas requirement.
- :exclamation: CORRECT about AKS control plane
  In an AKS cluster, we don't have to worry about the control plane components. They are managed by the AKS service. We can't access them directly. However, we can use the kubectl command to interact with them.
  ![AKS Cluster Components](https://learn.microsoft.com/en-us/azure/aks/media/concepts-clusters-workloads/control-plane-and-nodes.png)

- Kube-scheduler
  The main responsibility of kube-scheduler is to help newly created Pods to find a suitable node where they can run. There are many factors that kube-scheduler considers when making its decision, following are some examples:
  - individual and collective resource requirements (CPU, memory, storage, etc.)
  - hardware/software/policy constraints (AMD vs Intel, SSD vs HDD, etc.)
  - affinity and anti-affinity specifications
  - data locality
  - inter-workload interference and deadlines

## 2. Kubernetes Scheduler

In Kubernetes, *scheduling* refers to making sure that Pods are matched to Nodes to taht Kubelet can run them.

**Kube-scheduler** is the default scheduler for Kubernetes. You can also write your own scheduler. Kube-scheduler will select an optimal node for those not yet scheduled pods. Also, the API allows user to specify a node for a Pod when users create it. **Our focus today is figuring out how kube-scheduler achieves the above goals.**
- How Kube-scheduler find out the optimal node for a Pod?
- How to specify a node for a Pod when creating it?

### 2.1 Find out the optimal node for a Pod

The following steps will be taken by kube-scheduler to find out the optimal node for a Pod:
- Filtering
  At this step, kube-scheduler will filter out those nodes that don't meet the Pod's requirements. For example, if the Pod requires a minimum of 20 cores, then those nodes without enough cores will be filtered out. This is achieved by the **PodFitsResources** filter.
- Scoring
  Among those nodes that survived the filtering step, kube-scheduler will score and rank all the nodes. The optimal node will be the one with the highest score.

Finaly, kube-scheduler will bind the Pod to the optimal node. **If there are several nodes with the same rank (score), a random node will be selected.**

## 3. Scheduler Lab
### 3.1 Regular Pod Scheduling
Schedule a pod with super high CPU requirement so that no node can afford it

- `k run highcpu --image=nginx --dry-run=client -o yaml > HighCPU-Pending.yaml`
- `k top nodes`
- Add the following content
  ```yaml
  resources: 
      requests:
        cpu: "4000m"
  ```
- `k apply -f HighCPU-Pending.yaml`
- `k get po -w`
- `k describe po highcpu`

### 3.2 Pod Scheduling with NodeSelector
Schedule a pod to a specific node using nodeSelector.
- `k get nodes --show-labels`
- `k label node aks-nodepool1-15774875-vmss000000 nodecolor=red`
- `k label node aks-nodepool1-15774875-vmss000001 nodecolor=green`
- `k get nodes -l nodecolor=red`
- `k run rednginx --image=nginx --dry-run=client -o yaml > rednginx.yaml`
- Add the following content
  ```yaml
  nodeSelector:
    nodecolor: red
  ```
- `k apply -f rednginx.yaml`
- `k get po -w`
- `k get po -o wide`
- `k get node -l nodecolor=red`

### 3.3 Pod Scheduling with Node Affinity
Schedule a pod to nodes using node affinity
- Create a new nodepool
  ```bash
  az aks nodepool add \
  --resource-group k8sLearn \
  --cluster-name schedulerLab \
  --name silverpool \
  --node-count 2 \
  ```
- `k get nodes --show-labels`
- `k run affinitynginx --image=nginx --dry-run=client -o yaml > affinity-nginx.yaml`
- Add the following content
  ```yaml
    affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: agentpool
            operator: In
            values:
            - silverpool
  ```
- Schedule a pod using preferred node affinity
- `k get po -w`
- Change `silverpool` to `goldpool`
- `k apply -f affinity-nginx.yaml`
- Using `preferredDuringSchedulingIgnoredDuringExecution`
  ```yaml
  - weight: 1
    preference:
      matchExpressions:
      - key: agentpool
        operator: In
        values:
        - goldenpool
  ```
  - About weight:
    Higher weight means higher priority.
  - IgnoreDuringExection:
    This part means that the scheduling preferences are not reevaluated or considered once the pod is running. This behavior ensures that the pod remains stable and predictable during its execution, even if the node's conditions change.
- `k apply -f affinity-nginx.yaml`
- `k get po -o wide`

### 3.4 Pod Scheduler with Taints and Tolerations
Node affinity offers the property in pods that makes them more likely to be scheduled onto specific nodes. On the opposite side, **taints** are applied to nodes and enable a node to reject a set of pods. **tolerations** are applied to pods.

- Taint the node: 
  `k taint nodes aks-silverpool-68496876-vmss000000 color=blue:NoSchedule`
- `k edit node aks-silverpool-68496876-vmss000000`
  - Search for `taints`
- `k apply -f affinity-nginx.yaml`
  - Pod will be in pending state
- `k describe po affinitynginx`
  - Check why the pod is in pending state
- Add the following content to the `affinity-nginx.yaml` under `spec`
  ```yaml
  tolerations:
  - key: "nodecolor"
    operator: "Equal"
    value: "red"
    effect: "NoSchedule"
  ```