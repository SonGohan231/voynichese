import { handleNotes } from '../../../../lib/notebook-server';
export const dynamic='force-dynamic';
async function handler(request:Request,context:{params:Promise<{path?:string[]}>}){return handleNotes(request,(await context.params).path||[]);}
export {handler as GET,handler as PUT,handler as POST};
