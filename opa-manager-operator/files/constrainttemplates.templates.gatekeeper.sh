apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  creationTimestamp: null
  labels:
    controller-tools.k8s.io: "1.0"
    gatekeeper.sh/system: "yes"
  name: constrainttemplates.templates.gatekeeper.sh
spec:
  group: templates.gatekeeper.sh
  names:
    kind: ConstraintTemplate
    plural: constrainttemplates
  scope: Cluster
  subresources:
    status: {}
  validation:
    openAPIV3Schema:
      properties:
        apiVersion:
          description: 'APIVersion defines the versioned schema of this representation of an object. Servers should convert recognized schemas to the latest internal value, and may reject unrecognized values. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#resources'
          type: string
        kind:
          description: 'Kind is a string value representing the REST resource this object represents. Servers may infer this from the endpoint the client submits requests to. Cannot be updated. In CamelCase. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds'
          type: string
        metadata:
          type: object
        spec:
          properties:
            crd:
              properties:
                spec:
                  properties:
                    names:
                      properties:
                        kind:
                          type: string
                        shortNames:
                          items:
                            type: string
                          type: array
                      type: object
                    validation:
                      type: object
                  type: object
              type: object
            targets:
              items:
                properties:
                  libs:
                    items:
                      type: string
                    type: array
                  rego:
                    type: string
                  target:
                    type: string
                type: object
              type: array
          type: object
        status:
          properties:
            byPod:
              items:
                properties:
                  errors:
                    items:
                      properties:
                        code:
                          type: string
                        location:
                          type: string
                        message:
                          type: string
                      required:
                      - code
                      - message
                      type: object
                    type: array
                  id:
                    description: a unique identifier for the pod that wrote the status
                    type: string
                  observedGeneration:
                    format: int64
                    type: integer
                type: object
              type: array
            created:
              type: boolean
          type: object
  version: v1beta1
  versions:
  - name: v1beta1
    served: true
    storage: true
  - name: v1alpha1
    served: true
    storage: false
status:
  acceptedNames:
    kind: ""
    plural: ""
  conditions: []
  storedVersions: []