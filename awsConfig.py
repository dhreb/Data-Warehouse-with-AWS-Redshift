import configparser
import json
import pandas as pd
from create_clients import s3Client, ec2Client, iamClient, redshiftClient
from botocore.exceptions import ClientError

config = configparser.ConfigParser()
config.read("dwh.cfg")

DWH_IAM_ROLE_NAME = config["IAM_ROLE"]["NAME"]
DWH_DB = config["CLUSTER"]["DB_NAME"]
DWH_DB_USER = config["CLUSTER"]["DB_USER"]
DWH_DB_PASSWORD = config["CLUSTER"]["DB_PASSWORD"]
DWH_CLUSTER_IDENTIFIER = config["CLUSTER"]["CLUSTER_IDENTIFIER"]
DWH_CLUSTER_TYPE = config["CLUSTER"]["CLUSTER_TYPE"]
DWH_NUM_NODES = config["CLUSTER"]["NUM_NODES"]
DWH_NODE_TYPE = config["CLUSTER"]["NODE_TYPE"]
# DWH_IAM_ROLE_NAME = config["CLUSTER"]["DB_PORT"]

s3 = s3Client()
redshift = redshiftClient()
iam = iamClient()

def readS3Data():
    sampleDbBucket = s3.Bucket("udacity-dend")
    # for obj in sampleDbBucket.objects.filter(Prefix="ssbgz"):
    #     print(obj)
    for obj in sampleDbBucket.objects.all():
        print(obj)


def createIamRole():
    try:
        print("1.1 Creating a new IAM Role") 
        dwhRole = iam.create_role(
            Path='/',
            RoleName=DWH_IAM_ROLE_NAME,
            Description = "Allows Redshift clusters to call AWS services on your behalf.",
            AssumeRolePolicyDocument=json.dumps(
                {'Statement': [{'Action': 'sts:AssumeRole',
                  'Effect': 'Allow',
                  'Principal': {'Service': 'redshift.amazonaws.com'}}],
                'Version': '2012-10-17'})
        )    
    except Exception as e:
        print(e)
        
        
    print("1.2 Attaching Policy")

    iam.attach_role_policy(RoleName=DWH_IAM_ROLE_NAME,
                          PolicyArn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
                          )['ResponseMetadata']['HTTPStatusCode']

    print("1.3 Get the IAM role ARN")
    roleArn = iam.get_role(RoleName=DWH_IAM_ROLE_NAME)['Role']['Arn']

    print(roleArn)
    return roleArn

def createRedshiftCluster(roleArn):
  try:
    response = redshift.create_cluster(        
        #HW
        ClusterType=DWH_CLUSTER_TYPE,
        NodeType=DWH_NODE_TYPE,
        NumberOfNodes=int(DWH_NUM_NODES),

        #Identifiers & Credentials
        DBName=DWH_DB,
        ClusterIdentifier=DWH_CLUSTER_IDENTIFIER,
        MasterUsername=DWH_DB_USER,
        MasterUserPassword=DWH_DB_PASSWORD,
        
        #Roles (for s3 access)
        IamRoles=[roleArn]
    )
  except Exception as e:
      print(e)

def redshiftProps(props):
    pd.set_option('display.max_colwidth', None)
    keysToShow = ["ClusterIdentifier", "NodeType", "ClusterStatus", "MasterUsername", "DBName", "Endpoint", "NumberOfNodes", 'VpcId']
    x = [(k, v) for k,v in props.items() if k in keysToShow]
    print(pd.DataFrame(data=x, columns=["Key", "Value"]))

def main():
    # readS3Data()
    roleArn = createIamRole()
    createRedshiftCluster(roleArn)
    myClusterProps = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]
    redshiftProps(myClusterProps)

if __name__ == "__main__":
    main()