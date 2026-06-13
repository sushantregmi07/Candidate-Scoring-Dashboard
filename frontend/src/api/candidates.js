import client from "./client";

export async function listCandidates(params = {}) {
  const { data } = await client.get("/candidates", { params });
  return data;
}

export async function getCandidate(id) {
  const { data } = await client.get(`/candidates/${id}`);
  return data;
}

export async function submitScore(candidateId, payload) {
  const { data } = await client.post(
    `/candidates/${candidateId}/scores`,
    payload
  );
  return data;
}

export async function updateNotes(candidateId, notes) {
  const { data } = await client.patch(`/candidates/${candidateId}/notes`, {
    notes,
  });
  return data;
}

export async function generateSummary(candidateId) {
  const { data } = await client.post(`/candidates/${candidateId}/summary`);
  return data;
}
