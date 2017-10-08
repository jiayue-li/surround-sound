# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for updating target HTTPS proxies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificates_flags)
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class UpdateGA(base.SilentCommand):
  """Update a target HTTPS proxy.

  *{command}* is used to change the SSL certificate and/or URL map of
  existing target HTTPS proxies. A target HTTPS proxy is referenced
  by one or more forwarding rules which
  define which packets the proxy is responsible for routing. The
  target HTTPS proxy in turn points to a URL map that defines the rules
  for routing the requests. The URL map's job is to map URLs to
  backend services which handle the actual requests. The target
  HTTPS proxy also points to at most 10 SSL certificates used for
  server-side authentication.
  """

  SSL_CERTIFICATE_ARG = None
  SSL_CERTIFICATES_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    certs = parser.add_mutually_exclusive_group()
    cls.SSL_CERTIFICATE_ARG = (
        ssl_certificates_flags.SslCertificateArgumentForOtherResource(
            'target HTTPS proxy', required=False))
    cls.SSL_CERTIFICATE_ARG.AddArgument(parser, mutex_group=certs)
    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target HTTPS proxy', required=False))
    cls.SSL_CERTIFICATES_ARG.AddArgument(
        parser, mutex_group=certs, cust_metavar='SSL_CERTIFICATE')

    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument()
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='update')
    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        required=False, proxy_type='HTTPS')
    cls.URL_MAP_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.targetHttpsProxies

  @property
  def method(self):
    pass

  @property
  def resource_type(self):
    return 'targetHttpProxies'

  def _CreateRequestsWithCertRefs(self, args, ssl_cert_refs,
                                  quic_override=None):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    requests = []
    target_https_proxy_ref = self.TARGET_HTTPS_PROXY_ARG.ResolveAsResource(
        args, holder.resources)

    if ssl_cert_refs:
      requests.append(
          (client.apitools_client.targetHttpsProxies, 'SetSslCertificates',
           client.messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
               project=target_https_proxy_ref.project,
               targetHttpsProxy=target_https_proxy_ref.Name(),
               targetHttpsProxiesSetSslCertificatesRequest=(
                   client.messages.TargetHttpsProxiesSetSslCertificatesRequest(
                       sslCertificates=[
                           ref.SelfLink() for ref in ssl_cert_refs
                       ])))))

    if args.url_map:
      url_map_ref = self.URL_MAP_ARG.ResolveAsResource(args, holder.resources)
      requests.append(
          (client.apitools_client.targetHttpsProxies, 'SetUrlMap',
           client.messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
               project=target_https_proxy_ref.project,
               targetHttpsProxy=target_https_proxy_ref.Name(),
               urlMapReference=client.messages.UrlMapReference(
                   urlMap=url_map_ref.SelfLink()))))

    if quic_override:
      requests.append(
          (client.apitools_client.targetHttpsProxies, 'SetQuicOverride',
           client.messages.ComputeTargetHttpsProxiesSetQuicOverrideRequest(
               project=target_https_proxy_ref.project,
               targetHttpsProxy=target_https_proxy_ref.Name(),
               targetHttpsProxiesSetQuicOverrideRequest=(
                   client.messages.TargetHttpsProxiesSetQuicOverrideRequest(
                       quicOverride=quic_override)))))

    return client.MakeRequests(requests)

  def _GetSslCertificatesList(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    if args.ssl_certificate:
      log.warn(
          'The --ssl-certificate flag is deprecated and will be removed soon. '
          'Use equivalent --ssl-certificates %s flag.', args.ssl_certificate)
      return [
          self.SSL_CERTIFICATE_ARG.ResolveAsResource(args, holder.resources)
      ]

    if args.ssl_certificates:
      return self.SSL_CERTIFICATES_ARG.ResolveAsResource(args, holder.resources)

    return []

  def _CheckMissingArgument(self, args):
    if not (args.IsSpecified('ssl_certificates') or
            args.IsSpecified('ssl_certificate') or args.IsSpecified('url_map')):
      raise exceptions.ToolException(
          'You must specify at least one of [--ssl-certificates] or '
          '[--url-map].')

  def Run(self, args):
    self._CheckMissingArgument(args)

    ssl_certificate_refs = self._GetSslCertificatesList(args)
    return self._CreateRequestsWithCertRefs(args, ssl_certificate_refs)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateGA):
  """Update a target HTTPS proxy.

  *{command}* is used to change the SSL certificate and/or URL map of
  existing target HTTPS proxies. A target HTTPS proxy is referenced
  by one or more forwarding rules which
  define which packets the proxy is responsible for routing. The
  target HTTPS proxy in turn points to a URL map that defines the rules
  for routing the requests. The URL map's job is to map URLs to
  backend services which handle the actual requests. The target
  HTTPS proxy also points to at most 10 SSL certificates used for
  server-side authentication.
  """

  @classmethod
  def Args(cls, parser):
    super(UpdateAlpha, cls).Args(parser)
    target_proxies_utils.AddQuicOverrideUpdateArgs(parser)

  def _CheckMissingArgument(self, args):
    if not (args.IsSpecified('ssl_certificates') or
            args.IsSpecified('ssl_certificate') or
            args.IsSpecified('url_map') or args.IsSpecified('quic_override')):
      raise exceptions.ToolException(
          'You must specify at least one of [--ssl-certificates], '
          '[--url-map] or [--quic-override].')

  def Run(self, args):
    self._CheckMissingArgument(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    quic_override = (messages.TargetHttpsProxiesSetQuicOverrideRequest.
                     QuicOverrideValueValuesEnum(args.quic_override)
                    ) if args.IsSpecified('quic_override') else None

    ssl_certificate_refs = self._GetSslCertificatesList(args)

    return self._CreateRequestsWithCertRefs(args, ssl_certificate_refs,
                                            quic_override)