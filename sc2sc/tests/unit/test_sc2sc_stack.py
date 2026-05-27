import aws_cdk as core
import aws_cdk.assertions as assertions

from sc2sc.sc2sc_stack import Sc2ScStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sc2sc/sc2sc_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Sc2ScStack(app, "sc2sc")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
