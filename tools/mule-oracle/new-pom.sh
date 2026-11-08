#!/usr/bin/env bash
# test/fixtures/apps/<name>/ に pom.xml と mule-artifact.json を書く。
#   tools/mule-oracle/new-pom.sh <app-dir> [http] [apikit] [vm] [os] [file] [sftp] [mcp] [a2a] [grpc] [salesforce] [sfcomposite] [sfpubsub] [db] [secure] [validation] [vectors] [wsc] [jmx] [oauth] [inference] [anypointmq] [pg] [sqlite] [oracle] [mysql]
#   pg / sqlite / oracle / mysql は JDBC ドライバ (Mule の sharedLibraries として DB コネクタに見せる)
# 版は ~/.m2 にあるもの (オフラインでビルドできるもの) に合わせてある。
set -eu
dir="$1"; shift
name="$(basename "$dir")"
dep() { # groupId artifactId version
  printf '        <dependency>\n            <groupId>%s</groupId>\n            <artifactId>%s</artifactId>\n            <version>%s</version>\n            <classifier>mule-plugin</classifier>\n        </dependency>\n' "$1" "$2" "$3"
}
deps=""
shared=""
plugdeps=""   # additionalPluginDependencies (コネクタが provided にしているライブラリ)
jar() { # groupId artifactId version (JDBC ドライバ: 依存に足し、共有ライブラリにする)
  deps+="$(printf '        <dependency>\n            <groupId>%s</groupId>\n            <artifactId>%s</artifactId>\n            <version>%s</version>\n        </dependency>' "$1" "$2" "$3")"$'\n'
  shared+="$(printf '                        <sharedLibrary>\n                            <groupId>%s</groupId>\n                            <artifactId>%s</artifactId>\n                        </sharedLibrary>' "$1" "$2")"$'\n'
}
for m in "$@"; do
  case "$m" in
    http)   deps+="$(dep org.mule.connectors mule-http-connector 1.11.3)"$'\n' ;;
    apikit) deps+="$(dep org.mule.modules mule-apikit-module 1.12.6)"$'\n' ;;
    vm)     deps+="$(dep org.mule.connectors mule-vm-connector 2.0.2)"$'\n' ;;
    os)     deps+="$(dep org.mule.connectors mule-objectstore-connector 1.3.3)"$'\n' ;;
    sftp)   deps+="$(dep org.mule.connectors mule-sftp-connector 2.7.3)"$'\n' ;;
    mcp)    deps+="$(dep com.mulesoft.connectors mule-mcp-connector 1.5.0)"$'\n' ;;
    a2a)    deps+="$(dep com.mulesoft.connectors mule4-a2a-connector 1.1.1)"$'\n' ;;
    grpc)   deps+="$(dep com.mulesoft.connectors mule-grpc-connector 1.0.4)"$'\n' ;;
    file)   deps+="$(dep org.mule.connectors mule-file-connector 1.5.6)"$'\n' ;;
    salesforce) deps+="$(dep com.mulesoft.connectors mule-salesforce-connector 11.3.4)"$'\n' ;;
    sfcomposite) deps+="$(dep com.mulesoft.connectors mule-salesforce-composite-connector 3.1.4)"$'\n' ;;
    sfpubsub) deps+="$(dep com.mulesoft.connectors mule4-salesforce-pubsub-connector 1.4.2)"$'\n' ;;
    db)     deps+="$(dep org.mule.connectors mule-db-connector 1.16.4)"$'\n' ;;
    jmx)    deps+="$(dep com.demo-group mule-jmx-module 0.1.0)"$'\n' ;;
    oauth)  deps+="$(dep org.mule.modules mule-oauth-module 1.1.27)"$'\n' ;;
    inference) deps+="$(dep com.mulesoft.connectors mule4-inference-connector 1.2.0)"$'\n' ;;
    anypointmq) deps+="$(dep com.mulesoft.connectors anypoint-mq-connector 4.0.23)"$'\n' ;;
    secure) deps+="$(dep com.mulesoft.modules mule-secure-configuration-property-module 1.3.1)"$'\n' ;;
    validation) deps+="$(dep org.mule.modules mule-validation-module 2.0.11)"$'\n' ;;
    wsc)    deps+="$(dep org.mule.connectors mule-wsc-connector 2.2.2)"$'\n' ;;
    vectors) deps+="$(dep com.mulesoft.connectors mule4-vectors-connector 1.0.0)"$'\n'
             # langchain4j はコネクタの pom で provided なので、アプリが足す
             plugdeps+="$(printf '                        <plugin>\n                            <groupId>com.mulesoft.connectors</groupId>\n                            <artifactId>mule4-vectors-connector</artifactId>\n                            <additionalDependencies>\n')"$'\n'
             for a in langchain4j-core langchain4j; do
               plugdeps+="$(printf '                                <dependency>\n                                    <groupId>dev.langchain4j</groupId>\n                                    <artifactId>%s</artifactId>\n                                    <version>1.1.0</version>\n                                </dependency>' "$a")"$'\n'
             done
             plugdeps+="$(printf '                            </additionalDependencies>\n                        </plugin>')"$'\n' ;;
    pg)     jar org.postgresql postgresql 42.7.4 ;;
    sqlite) jar org.xerial sqlite-jdbc 3.50.3.0 ;;
    oracle) jar com.oracle.database.jdbc ojdbc11 23.8.0.25.04 ;;
    mysql)  jar com.mysql mysql-connector-j 9.2.0 ;;
    *) echo "unknown module: $m" >&2; exit 2 ;;
  esac
done
cat > "$dir/pom.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!-- mulay の golden シナリオ用アプリ。tools/mule-oracle/new-pom.sh で生成。 -->
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>mulay.fixtures</groupId>
    <artifactId>${name}</artifactId>
    <version>1.0.0</version>
    <packaging>mule-application</packaging>
    <name>${name}</name>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <app.runtime>4.11.3</app.runtime>
    </properties>

    <build>
        <plugins>
            <plugin>
                <groupId>org.mule.tools.maven</groupId>
                <artifactId>mule-maven-plugin</artifactId>
                <version>4.10.2</version>
                <extensions>true</extensions>
                <configuration>
                    <classifier>mule-application</classifier>
$( [ -n "$shared" ] && printf '                    <sharedLibraries>\n%s                    </sharedLibraries>' "$shared" )
$( [ -n "$plugdeps" ] && printf '                    <additionalPluginDependencies>\n%s                    </additionalPluginDependencies>' "$plugdeps" )
                </configuration>
            </plugin>
        </plugins>
    </build>

    <dependencies>
${deps}    </dependencies>

    <repositories>
        <repository>
            <id>anypoint-exchange-v3</id>
            <url>https://maven.anypoint.mulesoft.com/api/v3/maven</url>
        </repository>
        <repository>
            <id>mulesoft-releases</id>
            <url>https://repository.mulesoft.org/releases/</url>
        </repository>
    </repositories>
    <pluginRepositories>
        <pluginRepository>
            <id>mulesoft-releases</id>
            <url>https://repository.mulesoft.org/releases/</url>
            <snapshots><enabled>false</enabled></snapshots>
        </pluginRepository>
    </pluginRepositories>
</project>
EOF
cat > "$dir/mule-artifact.json" <<EOF
{
  "minMuleVersion": "4.10.0",
  "javaSpecificationVersions": ["17"]
}
EOF
