.. Metamorph documentation master file, created by
   sphinx-quickstart on Thu Mar  9 11:07:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Metamorph's documentation!
=====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



**Test metadata** term has many meanings. It could be **Test job metadata**, **Test run metadata**, **Test result metadata** or **Test report metadata**. The initial and major goal of **Metamorph** is to present the metadata of **test job** and **test run** into standard CI readable format.

The second major goal of **Metamorph** is to extend it's support for test harness and test automation frameworks.

Use Case
--------
Proposed tool solution shall be run before every CI job execution to provide needed test metadata. It will download/explore necessary test metadata and provide them a unified format.

Installation
------------
Installation is simple. Metamorph repository contains *setup.py* file with all needed dependencies. For Metamorph installation you need to run ``python setup.py install``.

Plugins
-------
Message bus reader
++++++++++++++++++
The purpose of this plugin is to sniff on CI message bus and get specific amount of CI messages.
Second use case of this plugin is to read given environmental variable which contain CI message. Messages are then stored into specified json file.

There are two ways how to run this plugin. First one is through CLI:

* for message:   ``python3 morph_messagehub.py message --user <user> --password <password> --host <host>``
* for environmental variable: ``python3 morph_messagehub.py env --env-variable <environmental-variable>``

Second variant is to use implemented ansible module:

* for message: ``ansible <host> -m messagehub -a "user=<user> password=<password> host=<host>"``
* for environmental  variable:  ``ansible <host> -m messagehub -a "env-variable=<environmental-variable>"``


Message data extractor
++++++++++++++++++++++
The aim of this plugin is to extract important metadata from CI messages like target, owners, release information and many more.

Easiest way to run this plugin is by:
``python3 message_data_extractor ci_message.json``

Extracted data are stored in json file.


Test tier status
++++++++++++++++
Purpose of this plugin is to provide information whether component build should be tagged with test tier number or not.
**Test tier status** plugin queries data from resultsDB and after metadata aggregation decides whether component build should be tagged or not.

How to run this plugin:

* with job_names provided: ``python3 morph_resultsdb.py --nvr name-version-release --test-tier 1 --resultsdb-api-url resultsdb-url [job_names]``
* without job_names: ``python3 morph_resultdsb.py --nvr name-version-release --test-tier 1 --resultsdb-api-url resultsdb-url``

and how to run resultsdb ansible module:

* with job_names provided: ``ansible <host> -m resultsdb -a "test_tier=1 nvr=name-version-release job_names=first-job,second-job resultsdb_api_url=resultsdb-url"``
* without job_names: ``ansible <host> -m resultsdb -a "test_tier=1 nvr=name-version-release resultsdb_api_url=resultsdb-url"``

Provision
+++++++++
Provision plugin purpose is to create topology files. These files will be handled by linch pin tool.
This plugin creates two files:
* topology.json - contains all data needed for provisioning
* topology_credentials.yaml - contains needed credentials for VM creation
These two files are created from openstack config file.

Provision plugin provides possibility to update topology values from metadata file and metadata location dictionary
configuration of metadata location:
key=path,to,metadata:
* key - topology field name
* metadata - name of searched metadata in path,to,metadata

How to run this plugin:
* without metadata specification: ``python3 morph_provision.py --git-repo <git-repository-path> --osp-config <osp-config-path>``
* with metadata specification: ``python3 morph_provision.py --git-repo <git-repository-path> --osp-config <osp-config-path> --metadata-file <metadata-file> --metadata-loc <metadata location>``

Metamorph for PDC
+++++++++++++++++
Metamorph for pdc plugin extracts all possible metadata from pdc by providing component nvr.
Product definition center (PDC) contains **Test provision metadata**, **Test run metadata** and **Test report metadata**
This makes PDC a really important metadata storage and obviously **Metamorph** needs to provide them.

How to execute metamorph for pdc:
``python metamorph/plugins/morph_pdc.py --component-nvr <component-name-version-release> --pdc-api-url <pdc-api-url>``

Execution pdc ansible module:
``ansible <host> -m pdc -a "component-nvr=<component-name-version-release> pdc-api-url=<pdc-api-url>"``


Message data extractor
++++++++++++++++++++++
The aim of this plugin is to extract important metadata from CI messages like target, owners, release information and many more.

Easiest way to run this plugin is by:
``python3 message_data_extractor ci_message.json``

Extracted data are stored in json file.


Provision
+++++++++
Provision plugin purpose is to create topology files. These files will be handled by linch pin tool.
This plugin creates two files:
* topology.json - contains all data needed for provisioning
* topology_credentials.yaml - contains needed credentials for VM creation
These two files are created from openstack config file.

Provision plugin provides possibility to update topology values from metadata file and metadata location dictionary
configuration of metadata location:
key=path,to,metadata:
* key - topology field name
* metadata - name of searched metadata in path,to,metadata

How to run this plugin:
* without metadata specification: ``python3 morph_provision.py --git-repo <git-repository-path> --osp-config <osp-config-path>``
* with metadata specification: ``python3 morph_provision.py --git-repo <git-repository-path> --osp-config <osp-config-path> --metadata-file <metadata-file> --metadata-loc <metadata location>``
