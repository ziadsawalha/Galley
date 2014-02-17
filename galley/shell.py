"""."""

import argparse
import os
import sys
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import yaml

from galley import builder


def main(argv=sys.argv[1:]):
    """Start galley command-line tool."""

    description = 'End-to-end testing orchestration with Docker.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'config',
        nargs='?',
        type=argparse.FileType('r'),
        help='Path to galley YAML file that defines Docker resources.',
        default=os.path.join(os.getcwd(), '.galley.yml'),
    )
    parser.add_argument(
        'pattern',
        nargs='?',
        help='Test file pattern.',
        default='galleytest_*.py',
    )
    parser.add_argument(
        '--no-destroy',
        action='store_true',
        help='Do not destroy images and containers.',
        dest='nodestroy',
        default=False,
    )
    args = parser.parse_args()

    config = yaml.load(args.config)
    builder.run_tests(config, args.pattern, args.nodestroy)
