import aws_cdk as core
import aws_cdk.assertions as assertions

from textract_project.textract_project_stack import TextractProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in textract_project/textract_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = TextractProjectStack(app, "textract-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
