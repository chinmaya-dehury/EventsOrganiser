# Events Organiser Ansible playbook
Partially automatic Events Organiser application setup for a Ubuntu 24.04 server. This playbook has only been tested on Ubuntu 24.04, it might not work on other distributions.

# Getting started
## Prerequisites
A few community modules need to be installed before the Ansible playbook can be run:
`ansible-galaxy collection install community.rabbitmq`
`ansible-galaxy collection install community.general`
`ansible-galaxy collection install kubernetes.core`

Some roles will also need additional variables to be set (passwords/secrets etc) so that they can work. You can do that with Ansible Vault, creating it in the same directory as the playbook, or through some other means.
You can create a vault file using `ansible-vault create vault.yml`
If a variable has a `.` in it, then that means you will need to nest the value inside a parent object. As an example, `parent.child` would need to be written in the configuration as the following:
```yml
parent:
    child: "value"
```

The list of required variables for each role is the following:

### Role - mysql
| Variable name | Description |
| - | - |
| mysql_conf_file | Location of the MySQL configuration file |
| mysql_root_password |  |
| events_org_secret.mysql_user_events_password |  |
| events_org_secret.mysql_user_microsoft_password |  |
| events_org_secret.mysql_user_auth_password |  |

### Role - rabbitmq
| Variable name | Description |
| - | - |
| is_kube_master_node | used to set up the control plane (kubeadm init, CNI install) |
| *user input* | continues the playbook after a manual intervention |

### Role - kubernetes
| Variable name | Description |
| - | - |
| is_kube_master_node | Boolean value that indicates whether the VM is a control plane or not |

### Role - app_setup_kubernetes
| Variable name | Description |
| - | - |
| domain_name | domain where all the APIs can be accessed & where the website will be hosted |
| events_org_config.dockerhub_username | Docker Hub username to pull images from |
| events_org_config.llm_gguf_url | URL to download the GGUF model from |
| events_org_config.mysql_host | IP address of the MySQL database |
| events_org_config.rabbitmq_host | IP address of the RabbitMQ broker |
| events_org_config.microsoft_app_client_id | Microsoft Entra application ID |
| events_org_secret.microsoft_app_secret | Microsoft Entra application secret |
| events_org_secret.microsoft_callback_secret | your own randomly generated string to verify that webhook notifications from Graph API are from Microsoft |
| events_org_secret.jwt_secret | random secret string that the auth microservice will generate JWTs with |
| events_org_secret.email_encryption_secret | a URL-safe base64-encoded 32-byte key for use with Fernet (use Fernet.generate_key() to create one) |
| events_org_secret.mysql_user_events_password | |
| events_org_secret.events_parser_rabbitmq_password | RabbitMQ user password for the events-parser user |
| events_org_secret.mysql_user_microsoft_password | |
| events_org_secret.mysql_user_auth_password | |

## Adding hosts
The VMs you want to set up have been split into two categories: controller and workers.
Controller is the control-plane for kubernetes and workers are VMs that join a kubernetes cluster.

Based on what you want each VM to do, put the server IPs either under `[controller]` or `[worker]` inside the hosts file. An example exists inside the `hosts` file

## Running the playbook
After setting up the hosts & variables, you can run the following command with the playbook (if you used Ansible Vault): `ansible-playbook --ask-vault-password -i inventory/hosts playbook.yml`

Some manual intervention is required for the `kubernetes` role