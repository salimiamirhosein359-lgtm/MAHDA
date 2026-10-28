import { redirect } from "next/navigation";

/* The Q&A experience moved to the full chatbot at /chat.
   Keep /ask as a permanent redirect so old links keep working. */
export default function AskPage() {
  redirect("/chat");
}
