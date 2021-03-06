properties([
    parameters ([
        string(name: 'DOCKER_REGISTRY_DOWNLOAD_URL', defaultValue: 'nexus-docker-private-group.ossim.io', description: 'Repository of docker images'),
    ]),
    pipelineTriggers([
            [$class: "GitHubPushTrigger"]
    ]),
    [$class: 'GithubProjectProperty', displayName: '', projectUrlStr: 'https://github.com/ossimlabs/ossim-geotiff'],
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '3', daysToKeepStr: '', numToKeepStr: '20')),
    disableConcurrentBuilds()
])
podTemplate(
  containers: [
    containerTemplate(
        name: 'git',
        image: 'alpine/git:latest',
        ttyEnabled: true,
        command: 'cat',
        envVars: [
            envVar(key: 'HOME', value: '/root')
        ]
    ),
    containerTemplate(
      name: 'builder',
      image: "${DOCKER_REGISTRY_DOWNLOAD_URL}/ossim-deps-builder-alpine:1.0",
      ttyEnabled: true,
      command: 'cat',
      privileged: true
    )
  ],
  volumes: [
    hostPathVolume(
      hostPath: '/var/run/docker.sock',
      mountPath: '/var/run/docker.sock'
    ),
  ]
)

{

node(POD_LABEL){
    stage("Checkout branch $BRANCH_NAME")
    {
        checkout(scm)
    }
    
    stage("Load Variables")
    {
      withCredentials([string(credentialsId: 'o2-artifact-project', variable: 'o2ArtifactProject')]) {
        step ([$class: "CopyArtifact",
          projectName: o2ArtifactProject,
          filter: "common-variables.groovy",
          flatten: true])
        }
        load "common-variables.groovy"
    }
//    stage ("Checkout proj")
//    {
//        sh """
//          ./checkout-proj.sh
//        """
//    }
//    stage ("Checkout geotiff")
//    {
//        sh """
//          ./checkout-geotiff.sh
//        """
//    }
    stage (" Build proj")
    {
        container('builder') 
        {
            sh """
              ./build-proj.sh
            """
        }
    }
    stage (" Build geotiff")
    {
        container('builder') 
        {
            sh """
              ./build-geotiff.sh
              cd /usr/local
              tar -czvf alpine-geotiff.tgz *
            """
        }
    }
    
    stage("Publish"){
        withCredentials([usernameColonPassword(credentialsId: 'nexusCredentials', variable: 'NEXUS_CREDENTIALS')]){
            container('builder') {
              sh """
              cd /usr/local
              curl -v -u ${NEXUS_CREDENTIALS} --upload-file alpine-geotiff.tgz https://nexus.ossim.io/repository/ossim-dependencies/"""
            }
          }
    }
    
	stage("Clean Workspace"){
      step([$class: 'WsCleanup'])
  }
}
}