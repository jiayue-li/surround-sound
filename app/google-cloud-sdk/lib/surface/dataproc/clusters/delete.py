# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Delete cluster command."""

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a cluster."""

  detailed_help = {
      'EXAMPLES': """\
          To delete a cluster, run:

            $ {command} my_cluster
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the cluster to delete.')
    base.ASYNC_FLAG.AddToParser(parser)
    util.AddTimeoutFlag(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = util.ParseCluster(args.name, dataproc)

    request = dataproc.messages.DataprocProjectsRegionsClustersDeleteRequest(
        clusterName=cluster_ref.clusterName,
        region=cluster_ref.region,
        projectId=cluster_ref.projectId)

    console_io.PromptContinue(
        message="The cluster '{0}' and all attached disks will be "
        'deleted.'.format(args.name),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.')

    operation = dataproc.client.projects_regions_clusters.Delete(request)

    if args.async:
      log.status.write(
          'Deleting [{0}] with operation [{1}].'.format(
              cluster_ref, operation.name))
      return operation

    operation = util.WaitForOperation(
        dataproc,
        operation,
        message='Waiting for cluster deletion operation',
        timeout_s=args.timeout)
    log.DeletedResource(cluster_ref)

    return operation
