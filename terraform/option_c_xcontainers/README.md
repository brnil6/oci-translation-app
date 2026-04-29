# Terraform Automation on Oracle Cloud : Create x Container Instances (private network) and a Loab Balancer (public network) to access them

This project has been designed to run with Oracle OCI Stacks Resource Manager. Nevertheless you can use it on another place but you have to uncomment some security variables needed outside of OCI Stacks Resource Manager. 

## Deploy to Oracle Cloud (but check prerequisites before)

Use the button below to open OCI Resource Manager with the packaged stack archive for this option:

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/brnil6/oci-translation-app/releases/download/v1.0.0/ocitranslator.zip)

The button uses the archive published at `terraform/option_c_xcontainers/ocitranslator.zip` on the `devkris` branch.

## Prerequisites

Before Starting you need to create a Secret in Oracle OCI Vault for being able to connect to the OCI Registry where your docker images for Container Instances are stored.

1) Create your Auth Token that will allow you to login in the OCIR Registry (The place where you will upload your docker image containing the translator agent)


2) Create the secret. It is a JSON String like below : 

{
"username": "charles-foster-kane",
"password": "<Your_Auth_Token>"
} 

3) Create a Dynamic Group for Container Instance in your compratment [Because Container Instance must be able to read the secret]
   
"Any {resource.type = 'computecontainerinstance', resource.compartment.id = 'ocid1.compartment.oc1..aaaa************qk5lyqgihqbjvhcxfakuruoyv4dr4utq7q'}"

4) Create a Policy to allow Container Instance read Secret

allow dynamic-group <dynamic-group-name> to read secret-bundles in compartment <compartment-name>

5) Create a Virtual Cloud Nework for your Container Instances. Use the default Action/Start the VCN Wizard on the UI Console after going to VCN. You will then create a public subnet that will be used by the Load Balancer and the private subnet that will be used by the Container Instances. 

6) Go to the public subnet and the private subnet to add the port 8000 as in ingress rule in the security list of the 2 subnets.

## Create the Stack

This project consider that your network configuration is done. It means : 
- VCN is created with a private subnet and a public subnet
- The security list of the public subnet has an ingress rule for the load balancer port
- The security list of the private subnet has an ingress rule for the container instances port

You can look at the variables and see : 
- Some of the variables have default values than can be updated by yourself or not as Stack Ressource Manager Variables
- Some other variables have no default value and are mandatory so you must know them.
  - compartment_ocid
  - region
  - private_subnet_ocid
  - public_subnet_ocid
  - ci_image_url
  - ci_registry_secret (ocid)
  - and so on...

## Scale

Very simple just use this variable : ci_count (= number of container instances)

Note : After running the Stack wait a little time to access to your backends using the Load Balancer. If you do not wait a little time you will have a "Bad Gateway" Message. This little time is needed by the LoadBalancer to validate Backends.
