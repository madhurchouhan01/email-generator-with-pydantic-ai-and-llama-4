from __future__ import annotations as _annotations
from dotenv import load_dotenv

load_dotenv()

from dataclasses import dataclass, field

from pydantic import BaseModel, EmailStr

from pydantic_ai import Agent
from pydantic_ai.format_as_xml import format_as_xml
from pydantic_ai.messages import ModelMessage
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

import asyncio

count = 0

@dataclass
class User:
    name: str
    email: EmailStr
    phone : int
    query: str


@dataclass
class Email:
    subject: str
    body: str


@dataclass
class State:
    user: User
    write_agent_messages: list[ModelMessage] = field(default_factory=list)
    latest_human_feedback: str | None = None

email_writer_agent = Agent(
    'groq:meta-llama/llama-4-scout-17b-16e-instruct',
    result_type=Email,
    system_prompt='Write an email on behalf of the user to Madhur Chouhan, Email : madhurchouhan02@gmail.com',
)


@dataclass
class WriteEmail(BaseNode[State]):
    email_feedback: str | None = None

    async def run(self, ctx: GraphRunContext[State]) -> Feedback:
        if self.email_feedback:
            prompt = (
                f'Rewrite the email for the user:\n'
                f'{format_as_xml(ctx.state.user)}\n'
                f'Feedback: {self.email_feedback}'
            )
        else:
            prompt = (
                f'Write an email on behalf of the user.:\n'
                f'{format_as_xml(ctx.state.user)}'
            )

        result = await email_writer_agent.run(
            prompt,
            message_history=ctx.state.write_agent_messages,
        )
        print('✉️  Email Generated : ')
        print(result.data)
        ctx.state.write_agent_messages += result.all_messages()
        return Feedback(result.data)


class EmailRequiresWrite(BaseModel):
    feedback: str


class EmailOk(BaseModel):
    pass


feedback_agent = Agent[None, EmailRequiresWrite | EmailOk](
    'groq:meta-llama/llama-4-scout-17b-16e-instruct',
    result_type=EmailRequiresWrite | EmailOk,  
    system_prompt=(
        'Review the email and provide feedback, email must reference the users query.'
    ),
)


@dataclass
class Feedback(BaseNode[State, None, Email]):
    email: Email

    async def run(self,ctx: GraphRunContext[State],) -> WriteEmail | End[Email]:
        global count 
        if count == 2:
            changes = input("Does this email look good? If yes, type : 'Yes' else, suggest changes: ")
            if changes.lower() == 'yes':
                return End(self.email)
            else:
                ctx.state.latest_human_feedback = changes  # ← Store feedback
                count = 0
                return WriteEmail(email_feedback=changes)
        count += 1
        prompt = format_as_xml({'user': ctx.state.user, 'email': self.email})
        result = await feedback_agent.run(prompt)
        print("✅ Feedback : ")
        print(result.data)
        if isinstance(result.data, EmailRequiresWrite):
            return WriteEmail(email_feedback=result.data.feedback)
        else:
            return End(self.email)


async def generate_email(name, email, phone, query):
    user = User(
        name=name,
        email=email,
        phone=phone,
        query=query,
    )
    state = State(user)
    feedback_graph = Graph(nodes=(WriteEmail, Feedback))
    result = await feedback_graph.run(WriteEmail(), state=state)

    """
    Email(
        subject='Welcome to our tech blog!',
        body='Hello John, Welcome to our tech blog! ...',
    )
    """
    return result.output


# output = asyncio.run(main('John Doe','john_doe@gmail.com','+91 9111025593','How did you get started in this field, and what has your career path been like so far?'))

