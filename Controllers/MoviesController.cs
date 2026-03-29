using EksiCaciklar.Data;
using EksiCaciklar.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EksiCaciklar.Controllers
{
    public class MoviesController : Controller
    {
        private readonly ApplicationDbContext _context;
        private readonly UserManager<IdentityUser> _userManager; // Değişkeni tanımladık

        // CONSTRUCTOR (YAPICI METOT) - İŞTE MOTOR BURASI
        public MoviesController(ApplicationDbContext context, UserManager<IdentityUser> userManager)
        {
            _context = context;
            _userManager = userManager; // <-- EĞER BU SATIR YOKSA PATLAR!
        }

        // GET: Movies
        public async Task<IActionResult> Index()
        {
            // İŞTE EKSİK OLAN KISIM BURASIYDI:
            // Veritabanındaki filmleri listeye çevirip View'a gönderiyoruz.
            // Parantez içi boş kalırsa o hata çıkar.
            return View(await _context.Movies.ToListAsync());
        }

        // GET: Movies/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null) return NotFound();

            var movie = await _context.Movies
                .Include(m => m.UserVotes)      // Artık hata vermez!
                    .ThenInclude(v => v.User)   // Yorumu yazanın adını getirmek için
                .FirstOrDefaultAsync(m => m.Id == id);

            if (movie == null) return NotFound();

            return View(movie);
        }

        // GET: Movies/Create
        [Authorize(Roles = "Admin")] // Sadece Admin girebilir!
        public IActionResult Create()
        {
            return View();
        }
        // POST: Movies/Create
        [HttpPost]
        [ValidateAntiForgeryToken]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Create([Bind("Id,Title,Description,Director,ImageUrl,ReleaseDate,ScoreScenario,ScoreActing,ScoreVisuals,ScoreSound,ScoreEditing")] Movie movie)
        {
            if (ModelState.IsValid)
            {
                // BURADAKİ UserScore = 0 SATIRINI SİLDİK!
                // Sadece VoteCount'u sıfırlıyoruz.
                // UserScore zaten formül olduğu için VoteCount 0 olunca otomatik 0 (veya -1) olur.
                movie.VoteCount = 0;

                // Detay ortalamalarını da 0 yapalım
                movie.UserAvgScenario = 0;
                movie.UserAvgActing = 0;
                movie.UserAvgVisuals = 0;
                movie.UserAvgSound = 0;
                movie.UserAvgEditing = 0;

                _context.Add(movie);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            return View(movie);
        }

        // GET: Movies/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null) return NotFound();

            var movie = await _context.Movies.FindAsync(id);
            if (movie == null) return NotFound();
            return View(movie);
        }

        // POST: Movies/Edit/5
        [HttpPost]
        [ValidateAntiForgeryToken]
        [Authorize] // Şimdilik sadece giriş yapanlar
        public async Task<IActionResult> Edit(int id, [Bind("Id,Title,Description,Director,ImageUrl,ReleaseDate,ScoreScenario,ScoreActing,ScoreVisuals,ScoreSound,ScoreEditing,UserScore,VoteCount")] Movie movie)
        {
            if (id != movie.Id) return NotFound();

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(movie);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!MovieExists(movie.Id)) return NotFound();
                    else throw;
                }
                return RedirectToAction(nameof(Index));
            }
            return View(movie);
        }

        //VOTE METODU
        [HttpPost]
        [Authorize]
        public async Task<IActionResult> Vote(int id, int sScenario, int sActing, int sVisuals, int sSound, int sEditing, string? comment)
        {
            var userId = _userManager.GetUserId(User);

            var existingVote = await _context.UserVotes
                .FirstOrDefaultAsync(v => v.MovieId == id && v.UserId == userId);

            if (existingVote != null)
            {
                // Güncelleme
                existingVote.ScoreScenario = sScenario;
                existingVote.ScoreActing = sActing;
                existingVote.ScoreVisuals = sVisuals;
                existingVote.ScoreSound = sSound;
                existingVote.ScoreEditing = sEditing;
                existingVote.Comment = comment; // Yorumu güncelle
                _context.Update(existingVote);
            }
            else
            {
                // Yeni Kayıt
                var newVote = new UserVote
                {
                    MovieId = id,
                    UserId = userId,
                    ScoreScenario = sScenario,
                    ScoreActing = sActing,
                    ScoreVisuals = sVisuals,
                    ScoreSound = sSound,
                    ScoreEditing = sEditing,
                    Comment = comment // Yorumu kaydet
                };
                _context.Add(newVote);
            }

            await _context.SaveChangesAsync();

            // --- FİLMİN ORTALAMALARINI GÜNCELLE ---
            var movie = await _context.Movies.FindAsync(id);

            if (movie != null) // Null Hatasını önleyen kontrol
            {
                var allVotes = await _context.UserVotes.Where(v => v.MovieId == id).ToListAsync();

                if (allVotes.Any())
                {
                    movie.VoteCount = allVotes.Count;

                    // DİKKAT: Burada UserScore'a atama yapmıyoruz!
                    // Sadece alt detayları güncelliyoruz.
                    movie.UserAvgScenario = allVotes.Average(v => v.ScoreScenario);
                    movie.UserAvgActing = allVotes.Average(v => v.ScoreActing);
                    movie.UserAvgVisuals = allVotes.Average(v => v.ScoreVisuals);
                    movie.UserAvgSound = allVotes.Average(v => v.ScoreSound);
                    movie.UserAvgEditing = allVotes.Average(v => v.ScoreEditing);
                }

                _context.Update(movie);
                await _context.SaveChangesAsync();
            }

            return RedirectToAction("Details", new { id = id });
        }

        // GET: Movies/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null) return NotFound();

            var movie = await _context.Movies
                .FirstOrDefaultAsync(m => m.Id == id);
            if (movie == null) return NotFound();

            return View(movie);
        }

        // POST: Movies/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var movie = await _context.Movies.FindAsync(id);
            if (movie != null)
            {
                _context.Movies.Remove(movie);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool MovieExists(int id)
        {
            return _context.Movies.Any(e => e.Id == id);
        }
    }
}