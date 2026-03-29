using EksiCaciklar.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EksiCaciklar.Controllers
{
    // BU SAYFAYA SADECE ADMINLER GİREBİLİR!
    [Authorize(Roles = "Admin")]
    public class UsersController : Controller
    {
        private readonly UserManager<IdentityUser> _userManager;

        public UsersController(UserManager<IdentityUser> userManager)
        {
            _userManager = userManager;
        }

        // Tüm kullanıcıları listele
        public async Task<IActionResult> Index()
        {
            var users = await _userManager.Users.ToListAsync();
            var userViewModels = new List<UserViewModel>();

            foreach (var user in users)
            {
                var thisViewModel = new UserViewModel();
                thisViewModel.UserId = user.Id;
                thisViewModel.Email = user.Email;
                thisViewModel.UserName = user.UserName;

                // Bu kullanıcı "Admin" rolünde mi?
                thisViewModel.IsAdmin = await _userManager.IsInRoleAsync(user, "Admin");

                userViewModels.Add(thisViewModel);
            }

            return View(userViewModels);
        }

        // Admin yap veya Adminliği geri al
        [HttpPost]
        public async Task<IActionResult> ToggleAdmin(string userId)
        {
            var user = await _userManager.FindByIdAsync(userId);
            if (user == null) return NotFound();

            // Zaten admin ise -> Adminliği al (User yap)
            if (await _userManager.IsInRoleAsync(user, "Admin"))
            {
                await _userManager.RemoveFromRoleAsync(user, "Admin");
            }
            // Admin değilse -> Admin yap
            else
            {
                await _userManager.AddToRoleAsync(user, "Admin");
            }

            return RedirectToAction("Index");
        }
    }
}