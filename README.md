# S3 Synchronization API <!-- omit in toc -->

An exercise to synchronize a local folder with an s3 storage engine. A dev environment can be setup with vagrant and Docker, where we use a minio s3 storage.

The API is developed with the flask python module, and the s3 client uses boto3.

- [Pre-requisites](#pre-requisites)
- [Setup](#setup)
- [API usage](#api-usage)

## Pre-requisites
- [Vagrant](https://www.vagrantup.com/)
- [Virtual Box](https://www.virtualbox.org/)
- [Ansible](https://www.ansible.com/)

## Setup

In order to initialize your environment, you only need to bring up your VM. The provisioning will be automatic, and it may spend multiple minutes:

```shell
vagrant up
```

At the end, you will have a file named **.env** being created in your project directory. Here is the description of each environment variable:
- **$API_PORT**: the API port mapped between Docker and your VM host.
- **$MINIO_PORT**: the minio port mapped between Docker and your VM host.
- **$MINIO_ACCESS_KEY**: an automatically generated access key.
- **$MINIO_SECRET_KEY**: an automatically generated secret key.

These s3 credentials are transfered into the API through environment variables.

Also, you will see a new directory located at **app/uploads**. This is where are located the files you can transfer to the S3 storage. You can edit, delete or add files in this folder, they are anyway ignored for the git commits.

## API usage

Once the environment is deployed and provisioned, you can use one of these routes:

- **/sync**: allows to start a synchronisation job. Here are the allowed parameters:
  - **source**: the relative local path (to *app/uploads*) of the directory to synchronize. Please note that if the directory doesn't exist or if it is empty, the bucket is deleted. By default it is the whole uploads directory.
  - **dest**: the s3 destination, in other terms the bucket name. Default value: *mybucket*.
  - **storage_url**: the s3 storage URL. By default is connects to the minio container.
  - **access_key**: the s3 access key.
  - **secret_key**: the s3 secret key.
  - **wait**: by default 0, but we can set a time sleeping in seconds between each file operation, in order to test job monitoring and cancellation.
- **/runnings**: displays all running synchronisations with their status.
- **/get**: displays a synchronisation status, with an **id** parameter.
- **/cancel**: cancels a running synchronisation, with an **id** parameter. Please note this will cancel the next file operation, and not the current one.

You can simply test the API with a web browser on http://localhost:5000.