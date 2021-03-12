#!/usr/bin/env python3

import logging
import yaml
from pathlib import Path
from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus

logger = logging.getLogger(__name__)


class OPAManagerCharm(CharmBase):
    """
    A Juju Charm for Spark
    """

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)
        self.framework.observe(self.on.stop, self._on_stop)
        self.framework.observe(self.on.install, self._on_install)
        self._stored.set_default(things=[])

    def _on_config_changed(self, _):
        """
        Set a new Juju pod specification
        """
        self._configure_pod()

    def _on_stop(self, _):
        """
        Mark unit is inactive
        """
        self.unit.status = MaintenanceStatus("Pod is terminating.")
        logger.info("Pod is terminating.")

    def _on_install(self, event):
        logger.info("Congratulations, the charm was properly installed!")

    def _on_update_status(self, event):
        logger.info("Status updated")

    def _build_pod_spec(self):
        """
        Construct a Juju pod specification for Spark
        """
        logger.debug("Building Pod Spec")
        crds = []
        try:
            crds = [
                yaml.load(Path(f).read_text())
                for f in [
                    "files/configs.config.gatekeeper.sh.yaml",
                    "files/constrainttemplates.templates.gatekeeper.sh.yaml",
                    "files/constraintpodstatuses.status.gatekeeper.sh.yaml",
                    "files/constrainttemplatepodstatuses.status.gatekeeper.sh.yaml",
                    # "files/sync.yaml",
                ]
            ]
        except yaml.YAMLError as exc:
            print("Error in configuration file:", exc)
        # rules = {}
        # try:
        #     rules = yaml.load(
        #         open(Path("files/rbac.yaml"), "r"), Loader=yaml.FullLoader
        #     )
        # except yaml.YAMLError as exc:
        #     print("Error in configuration file:", exc)
        config = self.model.config
        spec = {
            "version": 3,
            "kubernetesResources": {
                # "pod": {
                #     "serviceAccountName": "gatekeeper-admin",
                # },
                "customResourceDefinitions": [
                    {
                        "name": crd["metadata"]["name"],
                        "spec": crd["spec"],
                    }
                    for crd in crds
                ],
                "serviceAccounts":
                    {
                        "automountServiceAccountToken": True,
                        "roles": [
                            {
                                "global": False,
                                "rules": [
                                    {
                                        "apiGroups": [""],
                                        "resources": ["events"],
                                        "verbs": ["create", "patch"],
                                    },
                                    {
                                        "apiGroups": [""],
                                        "resources": ["secrets"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },{

                                        "apiGroups": ["*"],
                                        "resources": ["*"],
                                        "verbs": ["get", "list", "watch"],
                                    },
                                    {
                                        "apiGroups": ["apiextensions.k8s.io"],
                                        "resources": ["customresourcedefinitions"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },
                                    {
                                        "apiGroups": ["config.gatekeeper.sh"],
                                        "resources": ["configs"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },
                                    {
                                        "apiGroups": ["config.gatekeeper.sh"],
                                        "resources": ["configs/status"],
                                        "verbs": ["get", "patch", "update"],
                                    },
                                    {
                                        "apiGroups": ["constraints.gatekeeper.sh"],
                                        "resources": ["*"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },
                                    {
                                        "apiGroups": ["policy"],
                                        "resourceNames": ["gatekeeper-admin"],
                                        "resources": ["podsecuritypolicies"],
                                        "verbs": ["use"],
                                    },
                                    {
                                        "apiGroups": ["status.gatekeeper.sh"],
                                        "resources": ["*"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },
                                    {
                                        "apiGroups": ["templates.gatekeeper.sh"],
                                        "resources": ["constrainttemplates"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },
                                    {
                                        "apiGroups": ["templates.gatekeeper.sh"],
                                        "resources": ["constrainttemplates/finalizers"],
                                        "verbs": ["delete", "get", "patch", "update"],
                                    },
                                    {
                                        "apiGroups": ["templates.gatekeeper.sh"],
                                        "resources": ["constrainttemplates/status"],
                                        "verbs": ["get", "patch", "update"],
                                    },
                                    {
                                        "apiGroups": ["admissionregistration.k8s.io"],
                                        "resourceNames": [
                                            "gatekeeper-validating-webhook-configuration"
                                        ],
                                        "resources": ["validatingwebhookconfigurations"],
                                        "verbs": [
                                            "create",
                                            "delete",
                                            "get",
                                            "list",
                                            "patch",
                                            "update",
                                            "watch",
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
            },
            "containers": [
                {
                    # "serviceAccountName": "gatekeeper-admin",
                    "envConfig": {
                        "POD_NAMESPACE": {
                                "field":  {
                                    "path": "metadata.namespace",
                                    "api-version": "v1",
                                    },
                        },
                        "POD_NAME": {
                            "field": {
                                "path": "metadata.name",
                                "api-version": "v1",
                            }
                        },
                    },
                    "imageDetails": {
                        "imagePath": config["imagePath"],
                    },
                    "ports": [
                        {"containerPort": 8888, "name": "metrics", "protocol": "TCP"},
                        {"containerPort": 9090, "name": "healthz", "protocol": "TCP"},
                    ],
                    "imagePullPolicy": config["imagePullPolicy"],
                    "name": self.app.name,
                    "args": self._cli_args(),
                    "command": ["/manager"],

                    "image": "openpolicyagent/gatekeeper:v3.2.3",


                    # "resources": {
                    #     "limits": {"cpu": "1000m", "memory": "512Mi"},
                    #     "requests": {"cpu": "100m", "memory": "256Mi"},
                    # },

                    "kubernetes": {
                        "livenessProbe": {"httpGet": {"path": "/healthz", "port": 9090}},
                        "readinessProbe": {"httpGet": {"path": "/readyz", "port": 9090}},
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "capabilities": {"drop": ["all"]},
                            "runAsGroup": 999,
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                        }
                    }
                },
            ],
        }

        # if config["securityContext"] != "" and config["securityContext"] != "{}":
        #     spec["containers"][0]["kubernetes"]["securityContext"] = config[
        #         "securityContext"
        #     ]

        # if config.get("metricsEnable", False):
        #     spec["containers"][0]["ports"].append(
        #         {
        #             "containerPort": config["metricsPort"],
        #             "name": "metrics",
        #         }
        #     )
        #     spec["containers"][0]["kubernetes"]["readinessProbe"] = {
        #         "failureThreshold": 30,
        #         "tcpSocket": {
        #             "port": config["metricsPort"],
        #         },
        #         "initialDelaySeconds": 1,
        #         "periodSeconds": 2,
        #         "successThreshold": 1,
        #         "timeoutSeconds": 30,
        #     }
        #     spec["containers"][0]["kubernetes"]["livenessProbe"] = {
        #         "failureThreshold": 30,
        #         "tcpSocket": {
        #             "port": config["metricsPort"],
        #         },
        #         "initialDelaySeconds": 15,
        #         "periodSeconds": 20,
        #         "successThreshold": 1,
        #         "timeoutSeconds": 30,
        #     }

        # if config.get("webhookEnable", False):
        #     spec["containers"][0]["volumeConfig"] = [
        #         {
        #             "name": "webhook-certs",
        #             "mountPath": "/etc/webhook-certs",
        #             "secret": {
        #                 "name": "spark-webhook-certs",
        #             },
        #         },
        #     ]
        print(f"Pod spec: {spec}")
        return spec

    def _cli_args(self):
        """
        Construct command line arguments for Spark
        """
        config = self.model.config

        args = [
            "--operation=audit",
            "--operation=status",
            "--logtostderr",
        ]

        # if config.get("metricsEnable", False):
        #     args.extend(
        #         [
        #             "-enable-metrics=" + str(config["metricsEnable"]),
        #             "-metrics-labels=" + config["metricsLabels"],
        #             "-metrics-port=" + str(config["metricsPort"]),
        #             "-metrics-endpoint=" + config["metricsEndpoint"],
        #             "-metrics-prefix=" + config["metricsPrefix"],
        #         ]
        #     )

        # if config.get("webhookEnable", False):
        #     args.extend(
        #         [
        #             "-enable-webhook=" + str(config["webhookEnable"]),
        #             "-webhook-svc-namespace=" + config["namespace"],
        #             "-webhook-port=" + str(config["webhookPort"]),
        #             "-webhook-svc-name="
        #             + self.unit.name.replace("/", "-")
        #             + "-webhook",
        #             "-webhook-config-name="
        #             + self.unit.name.replace("/", "-")
        #             + "-webhook-config",
        #             "-webhook-namespace-selector=" + config["webhookNamespaceSelector"],
        #         ]
        #     )

        # if config.get("webhookEnable", False) and config.get(
        #     "resourceQuotaEnforcement", False
        # ):
        #     args.append("-enable-resource-quota-enforcement=true")

        # if config["replicaCount"] > 1:
        #     args.extend(
        #         [
        #             "-leader-election=true",
        #             "-leader-election-lock-namespace="
        #             + (
        #                 config["leaderElectionLockNamespace"]
        #                 if config["leaderElectionLockNamespace"] != ""
        #                 else config["namespace"]
        #             ),
        #             "-leader-election-lock-name="
        #             + config["leaderElectionLockNamespace"],
        #         ]
        #     )

        return args

    def _spark_config(self):
        """
        Construct Spark configuration
        """
        config = self.model.config

        logger.debug("Spark config : {}".format(config))

        return yaml.dump(config)

    def _check_config(self):
        """
        Identify missing but required items in configuation
        :returns: list of missing configuration items (configuration keys)
        """
        logger.debug("Checking Config")
        config = self.model.config
        missing = []

        if not config.get("imagePath"):
            missing.append("imagePath")

        return missing

    def _configure_pod(self):
        """
        Setup a new Spark pod specification
        """
        logger.debug("Configuring Pod")
        missing_config = self._check_config()
        if missing_config:
            logger.error(
                "Incomplete Configuration : {}. "
                "Application will be blocked.".format(missing_config)
            )
            self.unit.status = BlockedStatus(
                "Missing configuration: {}".format(missing_config)
            )
            return

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        self.unit.status = MaintenanceStatus("Setting pod spec.")
        pod_spec = self._build_pod_spec()

        self.model.pod.set_spec(pod_spec)
        self.app.status = ActiveStatus()
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(OPAManagerCharm)
