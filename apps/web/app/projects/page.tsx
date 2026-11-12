"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Project = { id: string; name: string; created_at: string };

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [name, setName] = useState("");

  // Load projects; if not logged in, the API returns 401 → go to login
  useEffect(() => {
    api<Project[]>("/projects")
      .then(setProjects)
      .catch(() => router.push("/login"));
  }, [router]);

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    const project = await api<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    setProjects((prev) => [project, ...(prev ?? [])]);
    setName("");
  }

  async function deleteProject(id: string) {
    await api(`/projects/${id}`, { method: "DELETE" });
    setProjects((prev) => prev?.filter((p) => p.id !== id) ?? null);
  }

  async function logout() {
    await api("/auth/logout", { method: "POST" });
    router.push("/login");
  }

  if (!projects) return <p className="p-8">Loading…</p>;

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <Button variant="outline" onClick={logout}>
          Log out
        </Button>
      </div>

      <form onSubmit={createProject} className="flex gap-2">
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New project name"
          required
        />
        <Button type="submit">Create</Button>
      </form>

      {projects.length === 0 && (
        <p className="text-muted-foreground">No projects yet.</p>
      )}

      <div className="space-y-2">
        {projects.map((p) => (
          <Card key={p.id}>
            <CardContent className="flex items-center justify-between py-4">
              <Link href={`/projects/${p.id}`} className="hover:underline">
                {p.name}
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => deleteProject(p.id)}
              >
                Delete
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}
