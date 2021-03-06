#!/usr/bin/env python3
import os
import logging
import yaml
import utils
from pathlib import Path
from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus


from charmhelpers.core.hookenv import (
    log,
)
from jinja2 import Template


logger = logging.getLogger(__name__)


class CustomResourceDefintion(object):

    def __init__(self, name, spec):

        self._name = name
        self._spec = spec

    @property
    def spec(self):
        return self._spec
    @property
    def name(self):
        return self._name


class OPAManagerCharm(CharmBase):
    """
    A Juju Charm for OPA
    """

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)
        self.framework.observe(self.on.stop, self._on_stop)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.start, self._on_start)
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

    def _load_yaml_objects(self, files_list):
        yaml_objects = []
        try:
            yaml_objects = [
                yaml.load(Path(f).read_text())
                for f in files_list
            ]
        except yaml.YAMLError as exc:
            print("Error in configuration file:", exc)

        return yaml_objects

    def _on_install(self, event):
        logger.info("Congratulations, the charm was properly installed!")

    def _on_update_status(self, event):
        logger.info("Status updated")

    def _build_pod_spec(self):
        """
        Construct a Juju pod specification for OPA
        """
        logger.debug("Building Pod Spec")

        # Load Custom Resource Definitions
        crd_objects = [
            CustomResourceDefintion(crd['metadata']['name'], yaml.dump(crd['spec']))
            for crd in self._load_yaml_objects([
                    "files/configs.config.gatekeeper.sh.yaml",
                    "files/constrainttemplates.templates.gatekeeper.sh.yaml",
                    "files/constraintpodstatuses.status.gatekeeper.sh.yaml",
                    "files/constrainttemplatepodstatuses.status.gatekeeper.sh.yaml",
            ])
        ]

        # Load custom resources
        crs = [
            CustomResourceDefintion(cr['metadata']['name'], yaml.dump(cr))
            for cr in self._load_yaml_objects([
                "files/psp.yaml"
            ])
        ]

        config = self.model.config

        template_args = {
            'crds': crd_objects,
            'image_path': config["imagePath"],
            'imagePullPolicy': config["imagePullPolicy"],
            'app_name': self.app.name,
            'cli_args': self._cli_args(),
            'audit_cli_args': self._audit_cli_args(),
            'crs': crs,
            'namespace': os.environ['JUJU_MODEL_NAME']
        }

        template = self._render_jinja_template("files/pod-spec.yaml.jinja2", template_args)

        spec = yaml.load(template)
        return spec

    def _cli_args(self):
        """
        Construct command line arguments for OPA
        """
        config = self.model.config

        args = [
            "--operation=audit",
            "--operation=status",
            "--logtostderr",
            "--port=8443",
            "--logtostderr",
            f"--exempt-namespace={os.environ['JUJU_MODEL_NAME']}",
            "--operation=webhook",
        ]
        return args

    def _audit_cli_args(self):
        """
        Construct command line arguments for OPA
        """
        config = self.model.config

        args = [
            "--operation=audit",
            "--operation=status",
            "--logtostderr",
        ]

        return args

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

    def _render_jinja_template(self, template, ctx):
        spec_template = {}
        with open(template) as fh:
            spec_template = Template(fh.read())

        return spec_template.render(**ctx)

    def _on_start(self, event):
        config = self.model.config
        k8s_objects = self._load_yaml_objects([
            'files/psp.yaml'
        ])
        k8s_objects.append(
            yaml.load(
                self._render_jinja_template(
                    'files/sync.yaml.jinja2',
                    {'namespace': os.environ['JUJU_MODEL_NAME']}
                )
            )
        )
        log(f"K8s objects: {k8s_objects}")
        for k8s_object in k8s_objects:
            utils.create_k8s_object(os.environ['JUJU_MODEL_NAME'], k8s_object)

    def _configure_pod(self):
        """
        Setup a new OPA pod specification
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
